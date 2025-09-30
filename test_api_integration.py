#!/usr/bin/env python3

from components.api_client import APIClient, StreamlitAPIClient
import json


def test_basic_integration():
    print("Testing API Client Integration...")
    print("=" * 50)
    
    client = APIClient()
    
    print("1. Testing health check...")
    health_response = client.health_check()
    print(f"   Success: {health_response.success}")
    
    if health_response.success:
        print(f"   Status: {health_response.data.get('status', 'Unknown')}")
        print("   ✅ Backend is running and accessible")
    else:
        print(f"   Error: {health_response.error}")
        print(f"   Type: {health_response.error_type}")
        print("   ❌ Backend is not accessible")
        return False
    
    print("\n2. Testing session creation...")
    session_response = client.create_session("test_customer_integration")
    print(f"   Success: {session_response.success}")
    
    if session_response.success:
        session_data = session_response.data.get("session", {})
        session_id = session_data.get("session_id")
        print(f"   Session ID: {session_id}")
        print("   ✅ Session created successfully")
        
        print("\n3. Testing query processing...")
        query_response = client.query(
            "Hello, this is a test query for API integration", 
            session_id, 
            "test_customer_integration"
        )
        print(f"   Success: {query_response.success}")
        
        if query_response.success:
            response_text = query_response.data.get("response", "")
            model_used = query_response.data.get("model_used", "Unknown")
            response_time = query_response.data.get("response_time_ms", 0)
            
            print(f"   Model: {model_used}")
            print(f"   Response time: {response_time}ms")
            print(f"   Response: {response_text[:100]}...")
            print("   ✅ Query processed successfully")
            
            print("\n4. Testing session retrieval...")
            get_session_response = client.get_session(session_id)
            print(f"   Success: {get_session_response.success}")
            
            if get_session_response.success:
                retrieved_session = get_session_response.data.get("session", {})
                messages = retrieved_session.get("messages", [])
                print(f"   Messages in session: {len(messages)}")
                print("   ✅ Session retrieved successfully")
                
                print("\n5. Testing session export...")
                export_response = client.export_session(session_id)
                print(f"   Success: {export_response.success}")
                
                if export_response.success:
                    print("   ✅ Session exported successfully")
                    return True
                else:
                    print(f"   Export error: {export_response.error}")
                    return False
            else:
                print(f"   Get session error: {get_session_response.error}")
                return False
        else:
            print(f"   Query error: {query_response.error}")
            return False
    else:
        print(f"   Session creation error: {session_response.error}")
        return False


def test_streamlit_client():
    print("\n" + "=" * 50)
    print("Testing Streamlit API Client...")
    
    client = StreamlitAPIClient()
    
    print("\n1. Testing health check with error handling...")
    health_result = client.handle_response(client.health_check())
    
    if not health_result.get("error"):
        print("   ✅ Health check successful")
        
        print("\n2. Testing session creation with error handling...")
        session_result = client.create_session_with_error_handling("test_streamlit_customer")
        
        if not session_result.get("error"):
            session_id = session_result.get("session", {}).get("session_id")
            print(f"   ✅ Session created: {session_id}")
            
            print("\n3. Testing query with error handling...")
            query_result = client.query_with_error_handling(
                "Test query from Streamlit client", 
                session_id, 
                "test_streamlit_customer"
            )
            
            if not query_result.get("error"):
                print("   ✅ Query processed successfully")
                return True
            else:
                print(f"   ❌ Query failed: {query_result.get('message')}")
                return False
        else:
            print(f"   ❌ Session creation failed: {session_result.get('message')}")
            return False
    else:
        print(f"   ❌ Health check failed: {health_result.get('message')}")
        return False


if __name__ == "__main__":
    try:
        basic_success = test_basic_integration()
        streamlit_success = test_streamlit_client()
        
        print("\n" + "=" * 50)
        print("INTEGRATION TEST RESULTS:")
        print(f"Basic API Client: {'✅ PASSED' if basic_success else '❌ FAILED'}")
        print(f"Streamlit API Client: {'✅ PASSED' if streamlit_success else '❌ FAILED'}")
        
        if basic_success and streamlit_success:
            print("\n🎉 All tests passed! API integration is working correctly.")
        else:
            print("\n⚠️ Some tests failed. Please check the backend API status.")
            
    except Exception as e:
        print(f"\n❌ Test suite failed with exception: {e}")
        import traceback
        traceback.print_exc()