#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.api_client import APIClient, StreamlitAPIClient
import json


def test_api_client():
    print("Testing API Client...")
    
    client = APIClient()
    
    print("\n1. Testing health check...")
    health_response = client.health_check()
    print(f"Health check - Success: {health_response.success}")
    if health_response.success:
        print(f"Health data: {health_response.data}")
    else:
        print(f"Health error: {health_response.error} ({health_response.error_type})")
    
    print("\n2. Testing session creation...")
    session_response = client.create_session("test_customer_123")
    print(f"Session creation - Success: {session_response.success}")
    if session_response.success:
        session_id = session_response.data.get("session", {}).get("session_id")
        print(f"Created session: {session_id}")
        
        print("\n3. Testing query...")
        query_response = client.query("Hello, this is a test query", session_id, "test_customer_123")
        print(f"Query - Success: {query_response.success}")
        if query_response.success:
            print(f"Response: {query_response.data.get('response', 'No response')[:100]}...")
        else:
            print(f"Query error: {query_response.error} ({query_response.error_type})")
        
        print("\n4. Testing session retrieval...")
        get_session_response = client.get_session(session_id)
        print(f"Get session - Success: {get_session_response.success}")
        if get_session_response.success:
            messages = get_session_response.data.get("session", {}).get("messages", [])
            print(f"Session has {len(messages)} messages")
        else:
            print(f"Get session error: {get_session_response.error}")
    else:
        print(f"Session creation error: {session_response.error} ({session_response.error_type})")
    
    print("\n5. Testing metrics...")
    metrics_response = client.get_query_metrics()
    print(f"Metrics - Success: {metrics_response.success}")
    if metrics_response.success:
        print("Metrics retrieved successfully")
    else:
        print(f"Metrics error: {metrics_response.error}")


def test_streamlit_client():
    print("\n\nTesting Streamlit API Client...")
    
    client = StreamlitAPIClient()
    
    print("\n1. Testing health check with error handling...")
    health_result = client.handle_response(client.health_check())
    if health_result.get("error"):
        print(f"Health check failed: {health_result.get('message')} ({health_result.get('error_type')})")
    else:
        print("Health check successful")
    
    print("\n2. Testing session creation with error handling...")
    session_result = client.create_session_with_error_handling("test_customer_streamlit")
    if session_result.get("error"):
        print(f"Session creation failed: {session_result.get('message')} ({session_result.get('error_type')})")
    else:
        session_id = session_result.get("session", {}).get("session_id")
        print(f"Session created successfully: {session_id}")
        
        print("\n3. Testing query with error handling...")
        query_result = client.query_with_error_handling("Test query from Streamlit client", session_id, "test_customer_streamlit")
        if query_result.get("error"):
            print(f"Query failed: {query_result.get('message')} ({query_result.get('error_type')})")
        else:
            print(f"Query successful: {query_result.get('response', 'No response')[:100]}...")


if __name__ == "__main__":
    print("API Client Test Suite")
    print("=" * 50)
    
    try:
        test_api_client()
        test_streamlit_client()
        print("\n" + "=" * 50)
        print("Test completed!")
    except Exception as e:
        print(f"\nTest failed with exception: {e}")
        import traceback
        traceback.print_exc()