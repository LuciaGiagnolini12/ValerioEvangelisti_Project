#!/usr/bin/env python3
"""
Script to upload large .nq files to localhost SPARQL endpoint using SPARQL LOAD command.
Based on ResearchSpace "Working with Data" documentation.
"""

import requests
import os
import sys
from urllib.parse import quote

# Configuration - Update this path to your .nq file
NQ_FILE_PATH = "evangelisti_app/test_db/strutturaEvangelisti_HD1_new.nq"

# Target named graph URI - Only used for non-.nq files (like .ttl, .rdf, .nt)
# For .nq files, this is automatically set to None to preserve original named graphs
TARGET_GRAPH_URI = "http://evangelisti.org/data/strutturaEvangelisti_HD1"

# SPARQL endpoint configuration
SPARQL_ENDPOINT = "http://localhost:10214/sparql"
USERNAME = "admin"
PASSWORD = "admin"

def check_file_exists(file_path):
    """Check if the .nq file exists and is accessible."""
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return False
    
    if not os.path.isfile(file_path):
        print(f"Error: Path is not a file: {file_path}")
        return False
    
    print(f"File found: {file_path}")
    print(f"File size: {os.path.getsize(file_path)} bytes")
    return True

def get_absolute_file_path(file_path):
    """Convert relative path to absolute file URI."""
    abs_path = os.path.abspath(file_path)
    # Convert to file URI format
    file_uri = f"file://{abs_path}"
    return file_uri, abs_path

def create_sparql_load_query(file_uri, graph_uri=None):
    """Create SPARQL LOAD query for the .nq file."""
    if graph_uri:
        # Load into specific named graph
        query = f"LOAD <{file_uri}> INTO GRAPH <{graph_uri}>"
    else:
        # Load into default graph (for .nq files, this preserves the named graphs)
        query = f"LOAD <{file_uri}>"
    
    return query

def execute_sparql_update(query, endpoint, username, password):
    """Execute SPARQL UPDATE query against the endpoint."""
    headers = {
        'Content-Type': 'application/sparql-update; charset=UTF-8',
        'Accept': 'text/boolean'
    }
    
    try:
        print(f"Executing SPARQL UPDATE query:")
        print(f"Query: {query}")
        print(f"Endpoint: {endpoint}")
        
        response = requests.post(
            endpoint,
            data=query,
            headers=headers,
            auth=(username, password),
            timeout=300  # 5 minutes timeout for large files
        )
        
        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✓ Data loaded successfully!")
            return True
        else:
            print(f"✗ Error loading data. Status code: {response.status_code}")
            print(f"Response text: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("✗ Request timed out. The file might be too large or the server is slow.")
        return False
    except requests.exceptions.ConnectionError:
        print("✗ Connection error. Make sure the SPARQL endpoint is running.")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {str(e)}")
        return False

def create_drop_graph_query(graph_uri):
    """Create SPARQL query to drop/clear a named graph."""
    return f"DROP GRAPH <{graph_uri}>"

def is_nquads_file(file_path):
    """Check if the file is an N-Quads (.nq) file based on extension."""
    return file_path.lower().endswith('.nq')

def main():
    """Main function to upload the .nq file."""
    print("=== Large RDF File Upload Script ===")
    print(f"Target file: {NQ_FILE_PATH}")
    print(f"SPARQL endpoint: {SPARQL_ENDPOINT}")
    
    # Check if file exists
    if not check_file_exists(NQ_FILE_PATH):
        sys.exit(1)
    
    # Determine if this is an .nq file and adjust target graph accordingly
    is_nq_file = is_nquads_file(NQ_FILE_PATH)
    effective_target_graph = None if is_nq_file else TARGET_GRAPH_URI
    
    if is_nq_file:
        print("📋 Detected N-Quads (.nq) file - will preserve original named graphs")
        print("Target graph: Preserve original named graphs from .nq file")
    elif effective_target_graph:
        print(f"Target graph: {effective_target_graph}")
    else:
        print("Target graph: Default graph")
    print()
    
    # Get absolute file path and URI
    file_uri, abs_path = get_absolute_file_path(NQ_FILE_PATH)
    print(f"Absolute path: {abs_path}")
    print(f"File URI: {file_uri}")
    print()
    
    # If target graph is specified and it's not an .nq file, ask if user wants to clear it first
    if effective_target_graph and not is_nq_file:
        clear_graph = input(f"Do you want to clear the target graph '{effective_target_graph}' before loading? (y/N): ").strip().lower()
        if clear_graph in ['y', 'yes']:
            print(f"\nClearing target graph: {effective_target_graph}")
            drop_query = create_drop_graph_query(effective_target_graph)
            print(f"Executing: {drop_query}")
            
            # Execute drop query (it's OK if it fails - graph might not exist)
            try:
                execute_sparql_update(drop_query, SPARQL_ENDPOINT, USERNAME, PASSWORD)
                print("✓ Graph cleared (or didn't exist)")
            except:
                print("ℹ Graph might not have existed - continuing with load")
            print()
    
    # Create SPARQL LOAD query
    query = create_sparql_load_query(file_uri, effective_target_graph)
    
    # Confirm before proceeding
    print("About to execute the following SPARQL UPDATE:")
    print(f"  {query}")
    print()
    
    confirm = input("Do you want to proceed with the data load? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("Operation cancelled.")
        sys.exit(0)
    
    # Execute the query
    print("\nStarting data upload...")
    success = execute_sparql_update(query, SPARQL_ENDPOINT, USERNAME, PASSWORD)
    
    if success:
        print("\n🎉 Upload completed successfully!")
        print("\nYou can now query your data using the SPARQL endpoint.")
        
        if is_nq_file:
            print("\nUseful queries for your N-Quads data:")
            print("  # List all named graphs and their triple counts:")
            print("  SELECT ?graph (COUNT(*) as ?triples) WHERE { GRAPH ?graph { ?s ?p ?o } } GROUP BY ?graph ORDER BY DESC(?triples)")
            print()
            print("  # List graphs from your Evangelisti archive:")
            print('  SELECT ?graph (COUNT(*) as ?triples) WHERE { GRAPH ?graph { ?s ?p ?o } FILTER(STRSTARTS(STR(?graph), "http://example.org/ArchivioEvangelisti/")) } GROUP BY ?graph ORDER BY DESC(?triples)')
            print()
            print("  # Count total triples across all graphs:")
            print("  SELECT (COUNT(*) as ?totalTriples) WHERE { ?s ?p ?o }")
            print()
            print("  # Sample some triples to see what's loaded:")
            print("  SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10")
        elif effective_target_graph:
            print("Example queries to check loaded data:")
            print(f"  # Count triples in your specific graph:")
            print(f"  SELECT (COUNT(*) as ?triples) WHERE {{ GRAPH <{effective_target_graph}> {{ ?s ?p ?o }} }}")
            print(f"  # Drop the graph when needed:")
            print(f"  DROP GRAPH <{effective_target_graph}>")
        else:
            print("Example query to check loaded data:")
            print("  SELECT (COUNT(*) as ?triples) WHERE { ?s ?p ?o }")
    else:
        print("\n❌ Upload failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
