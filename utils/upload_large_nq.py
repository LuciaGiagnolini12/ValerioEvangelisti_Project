#!/usr/bin/env python3
"""
Script to upload multiple .nq files from a folder to localhost SPARQL endpoint using SPARQL LOAD command.
Based on ResearchSpace "Working with Data" documentation.
"""

import requests
import os
import sys
import argparse
import glob
from urllib.parse import quote
from colorama import init, Fore, Style

# Initialize colorama for colored output
init(autoreset=True)

# Configuration
GRAPH_NAMESPACE = "http://ficlit.unibo.it/ArchivioEvangelisti/"  # Required namespace for all graphs
NQ_FOLDER_PATH = "evangelisti_app/test_db"  # Default folder containing .nq files

# SPARQL endpoint configuration
SPARQL_ENDPOINT = "http://localhost:10214/sparql"
USERNAME = "admin"
PASSWORD = "admin"

def print_success(message):
    """Print success message in green."""
    print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")

def print_error(message):
    """Print error message in red."""
    print(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")

def print_info(message):
    """Print info message in blue."""
    print(f"{Fore.BLUE}ℹ {message}{Style.RESET_ALL}")

def print_warning(message):
    """Print warning message in yellow."""
    print(f"{Fore.YELLOW}⚠ {message}{Style.RESET_ALL}")

def find_nq_files(folder_path):
    """Find all .nq files in the specified folder."""
    if not os.path.exists(folder_path):
        print_error(f"Folder not found: {folder_path}")
        return []
    
    if not os.path.isdir(folder_path):
        print_error(f"Path is not a folder: {folder_path}")
        return []
    
    # Find all .nq files in the folder
    nq_files = glob.glob(os.path.join(folder_path, "*.nq"))
    
    if not nq_files:
        print_warning(f"No .nq files found in folder: {folder_path}")
        return []
    
    print_info(f"Found {len(nq_files)} .nq file(s) in folder: {folder_path}")
    for file in nq_files:
        file_size = os.path.getsize(file)
        print(f"  - {os.path.basename(file)} ({file_size:,} bytes)")
    
    return nq_files

def extract_graph_names_from_nq(file_path):
    """Extract unique graph names from an .nq file."""
    graphs = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # N-Quads format: <subject> <predicate> <object> <graph> .
                # Find the last < > pair which should be the graph
                parts = line.split('>')
                if len(parts) >= 4:
                    # Find the graph URI (usually the 4th <...> in the line)
                    graph_start = line.rfind('<')
                    if graph_start > 0:
                        graph_end = line.find('>', graph_start)
                        if graph_end > graph_start:
                            graph_uri = line[graph_start+1:graph_end]
                            graphs.add(graph_uri)
                
                # Sample first 1000 lines to avoid reading huge files entirely
                if line_num >= 1000:
                    print_info(f"  Sampled first 1000 lines from {os.path.basename(file_path)}")
                    break
                    
    except Exception as e:
        print_error(f"Error reading file {file_path}: {str(e)}")
    
    return graphs

def validate_graph_namespace(nq_files, required_namespace):
    """Validate that all graphs in all .nq files start with the required namespace."""
    print(f"\nValidating graph namespaces (required: {required_namespace})...")
    
    all_valid = True
    all_graphs = set()
    
    for file_path in nq_files:
        print(f"\nChecking: {os.path.basename(file_path)}")
        graphs = extract_graph_names_from_nq(file_path)
        
        if not graphs:
            print_warning(f"  No graphs found in file")
            continue
        
        valid_graphs = []
        invalid_graphs = []
        
        for graph in graphs:
            all_graphs.add(graph)
            if graph.startswith(required_namespace):
                valid_graphs.append(graph)
            else:
                invalid_graphs.append(graph)
                all_valid = False
        
        print(f"  Found {len(graphs)} unique graph(s)")
        if valid_graphs:
            print_success(f"  {len(valid_graphs)} graph(s) with correct namespace")
            for g in valid_graphs[:3]:  # Show first 3
                print(f"    - {g}")
            if len(valid_graphs) > 3:
                print(f"    ... and {len(valid_graphs) - 3} more")
        
        if invalid_graphs:
            print_error(f"  {len(invalid_graphs)} graph(s) with INVALID namespace")
            for g in invalid_graphs[:3]:  # Show first 3
                print(f"    - {g}")
            if len(invalid_graphs) > 3:
                print(f"    ... and {len(invalid_graphs) - 3} more")
    
    return all_valid, all_graphs

def get_absolute_file_path(file_path):
    """Convert relative path to absolute file URI."""
    abs_path = os.path.abspath(file_path)
    # Convert to file URI format
    file_uri = f"file://{abs_path}"
    return file_uri, abs_path

def create_sparql_load_query(file_uri):
    """Create SPARQL LOAD query for the .nq file."""
    # For .nq files, we don't specify a target graph to preserve original named graphs
    query = f"LOAD <{file_uri}>"
    return query

def execute_sparql_update(query, endpoint, username, password, timeout=300):
    """Execute SPARQL UPDATE query against the endpoint."""
    headers = {
        'Content-Type': 'application/sparql-update; charset=UTF-8',
        'Accept': 'text/boolean'
    }
    
    try:
        response = requests.post(
            endpoint,
            data=query,
            headers=headers,
            auth=(username, password),
            timeout=timeout
        )
        
        if response.status_code == 200:
            return True, "Success"
        else:
            return False, f"Status code: {response.status_code}, Response: {response.text}"
            
    except requests.exceptions.Timeout:
        return False, "Request timed out"
    except requests.exceptions.ConnectionError:
        return False, "Connection error - make sure the SPARQL endpoint is running"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def delete_graphs_with_namespace(namespace, endpoint, username, password):
    """Delete all graphs that start with the given namespace."""
    print(f"\nDeleting all graphs starting with: {namespace}")
    
    # First, get list of graphs to delete
    list_query = f"""
    SELECT DISTINCT ?graph 
    WHERE {{
        GRAPH ?graph {{ ?s ?p ?o }}
        FILTER(STRSTARTS(STR(?graph), "{namespace}"))
    }}
    """
    
    headers = {
        'Content-Type': 'application/sparql-query',
        'Accept': 'application/sparql-results+json'
    }
    
    try:
        # Get list of graphs
        response = requests.post(
            endpoint,
            data=list_query,
            headers=headers,
            auth=(username, password)
        )
        
        if response.status_code != 200:
            print_error(f"Failed to list graphs: {response.status_code}")
            return False
        
        results = response.json()
        graphs_to_delete = [binding['graph']['value'] for binding in results['results']['bindings']]
        
        if not graphs_to_delete:
            print_info("No graphs found with the specified namespace")
            return True
        
        print_info(f"Found {len(graphs_to_delete)} graph(s) to delete:")
        for graph in graphs_to_delete[:5]:  # Show first 5
            print(f"  - {graph}")
        if len(graphs_to_delete) > 5:
            print(f"  ... and {len(graphs_to_delete) - 5} more")
        
        # Delete each graph
        deleted_count = 0
        for graph in graphs_to_delete:
            drop_query = f"DROP GRAPH <{graph}>"
            success, message = execute_sparql_update(drop_query, endpoint, username, password, timeout=60)
            if success:
                deleted_count += 1
            else:
                print_warning(f"Failed to delete graph {graph}: {message}")
        
        print_success(f"Deleted {deleted_count}/{len(graphs_to_delete)} graphs")
        return deleted_count == len(graphs_to_delete)
        
    except Exception as e:
        print_error(f"Error during graph deletion: {str(e)}")
        return False

def upload_nq_file(file_path, endpoint, username, password):
    """Upload a single .nq file."""
    file_uri, abs_path = get_absolute_file_path(file_path)
    query = create_sparql_load_query(file_uri)
    
    print(f"\nUploading: {os.path.basename(file_path)}")
    print(f"  File URI: {file_uri}")
    
    success, message = execute_sparql_update(query, endpoint, username, password, timeout=600)
    
    if success:
        print_success(f"  Uploaded successfully")
        return True
    else:
        print_error(f"  Upload failed: {message}")
        return False

def main():
    """Main function to upload multiple .nq files."""
    parser = argparse.ArgumentParser(description='Upload multiple .nq files to SPARQL endpoint')
    parser.add_argument('--folder', '-f', default=NQ_FOLDER_PATH, 
                        help=f'Folder containing .nq files (default: {NQ_FOLDER_PATH})')
    parser.add_argument('--namespace', '-n', default=GRAPH_NAMESPACE,
                        help=f'Required graph namespace (default: {GRAPH_NAMESPACE})')
    parser.add_argument('--clear-namespace', '-c', action='store_true',
                        help='Clear all graphs with the namespace before uploading')
    parser.add_argument('--endpoint', '-e', default=SPARQL_ENDPOINT,
                        help=f'SPARQL endpoint URL (default: {SPARQL_ENDPOINT})')
    parser.add_argument('--username', '-u', default=USERNAME,
                        help=f'Username for authentication (default: {USERNAME})')
    parser.add_argument('--password', '-p', default=PASSWORD,
                        help='Password for authentication')
    
    args = parser.parse_args()
    
    print("=== Multiple N-Quads File Upload Script ===")
    print(f"Folder: {args.folder}")
    print(f"Required namespace: {args.namespace}")
    print(f"SPARQL endpoint: {args.endpoint}")
    print(f"Clear namespace first: {'Yes' if args.clear_namespace else 'No'}")
    
    # Find all .nq files
    nq_files = find_nq_files(args.folder)
    if not nq_files:
        sys.exit(1)
    
    # Validate graph namespaces
    all_valid, all_graphs = validate_graph_namespace(nq_files, args.namespace)
    
    if not all_valid:
        print_error("\nValidation failed! Not all graphs have the required namespace.")
        print_error("Upload process cannot begin.")
        sys.exit(1)
    
    print_success("\nAll graphs have the correct namespace! Upload process can begin.")
    
    # Clear namespace if requested
    if args.clear_namespace:
        print_warning(f"\nYou requested to clear all graphs starting with: {args.namespace}")
        confirm = input("Are you sure you want to delete these graphs? (y/N): ").strip().lower()
        if confirm in ['y', 'yes']:
            if delete_graphs_with_namespace(args.namespace, args.endpoint, args.username, args.password):
                print_success("Namespace cleared successfully")
            else:
                print_error("Failed to clear namespace completely")
                proceed = input("Do you want to continue with upload anyway? (y/N): ").strip().lower()
                if proceed not in ['y', 'yes']:
                    print("Operation cancelled.")
                    sys.exit(0)
        else:
            print("Skipping namespace clearing.")
    
    # Confirm upload
    print(f"\nAbout to upload {len(nq_files)} .nq file(s)")
    confirm = input("Do you want to proceed with the data load? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("Operation cancelled.")
        sys.exit(0)
    
    # Upload each file
    print("\nStarting data upload...")
    successful_uploads = 0
    failed_uploads = 0
    
    for file_path in nq_files:
        if upload_nq_file(file_path, args.endpoint, args.username, args.password):
            successful_uploads += 1
        else:
            failed_uploads += 1
    
    # Summary
    print("\n" + "="*50)
    print("UPLOAD SUMMARY")
    print("="*50)
    print_success(f"Successful uploads: {successful_uploads}")
    if failed_uploads > 0:
        print_error(f"Failed uploads: {failed_uploads}")
    
    if successful_uploads > 0:
        print("\n🎉 Upload completed!")
        print("\nUseful queries for your data:")
        print(f"  # List all graphs in your namespace:")
        print(f'  SELECT DISTINCT ?graph (COUNT(*) as ?triples) WHERE {{ GRAPH ?graph {{ ?s ?p ?o }} FILTER(STRSTARTS(STR(?graph), "{args.namespace}")) }} GROUP BY ?graph ORDER BY DESC(?triples)')
        print()
        print(f"  # Count total triples in your namespace:")
        print(f'  SELECT (COUNT(*) as ?totalTriples) WHERE {{ GRAPH ?graph {{ ?s ?p ?o }} FILTER(STRSTARTS(STR(?graph), "{args.namespace}")) }}')
        print()
        print(f"  # Delete all graphs in your namespace (when needed):")
        print(f'  DELETE WHERE {{ GRAPH ?g {{ ?s ?p ?o }} FILTER(STRSTARTS(STR(?g), "{args.namespace}")) }}')
    else:
        print("\n❌ All uploads failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
