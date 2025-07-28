# import asyncio
# from mcp.client.stdio import stdio_client
# from mcp import ClientSession, StdioServerParameters

# async def run_mcp_client():
#     # Adjust the command and args if you want to launch the MCP server as subprocess
#     # or configure to connect to a running server differently.
#     server_params = StdioServerParameters(
#         command="python",
#         args=["custom_server.py"],  # Adapt the path if needed to your MCP server file
#     )

#     async with stdio_client(server_params) as (reader, writer):
#         async with ClientSession(reader, writer) as session:
#             await session.initialize()

#             # List available tools (for debug)
#             tools_resp = await session.list_tools()
#             print(f"Available tools: {[tool.name for tool in tools_resp.tools]}")

#             # Call your search_jobs tool with a test query
#             response = await session.call_tool("search_jobs", {"query": "Software Engineer Bangalore"})
#             print("Search result:")
#             print(response)

# if __name__ == "__main__":
#     asyncio.run(run_mcp_client())


import subprocess
import time
import asyncio
import httpx
import os
import signal

def kill_process_on_port(port=8000):
    """Kill any process using the specified port"""
    try:
        print(f"🔍 Checking for processes on port {port}...")
        
        # Find process using the port
        result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        pids_to_kill = []
        for line in lines:
            if f':{port}' in line and 'LISTENING' in line:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    pids_to_kill.append(pid)
                    print(f"   Found process {pid} using port {port}")
        
        if pids_to_kill:
            for pid in pids_to_kill:
                try:
                    subprocess.run(['taskkill', '/F', '/PID', pid], check=True)
                    print(f"✅ Killed process {pid}")
                except subprocess.CalledProcessError as e:
                    print(f"⚠️  Could not kill process {pid}: {e}")
            
            # Wait a moment for the port to be released
            time.sleep(2)
            return True
        else:
            print(f"   No processes found on port {port}")
            return False
            
    except Exception as e:
        print(f"❌ Error managing processes: {e}")
        return False

def start_nlweb_service():
    """Start the NLWeb service"""
    nlweb_path = r"C:\Users\RACHANAA\OneDrive - Virtusa\Desktop\NLWeb\NLWeb\code"
    
    print(f"🚀 Starting NLWeb service from {nlweb_path}...")
    
    # Check if the directory exists
    if not os.path.exists(nlweb_path):
        print(f"❌ Directory not found: {nlweb_path}")
        return None
    
    # Check if app-file.py exists
    app_file = os.path.join(nlweb_path, "app-file.py")
    if not os.path.exists(app_file):
        print(f"❌ app-file.py not found at {app_file}")
        return None
    
    try:
        # Start the service
        process = subprocess.Popen(
            ['python', 'app-file.py'],
            cwd=nlweb_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        print(f"✅ Started NLWeb service (PID: {process.pid})")
        print("⏳ Waiting for service to initialize...")
        
        # Wait a bit for the service to start
        time.sleep(5)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ Service appears to be running")
            return process
        else:
            # Process terminated, get error output
            stdout, stderr = process.communicate()
            print("❌ Service failed to start")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Error starting service: {e}")
        return None

async def test_nlweb_endpoints():
    """Test NLWeb service endpoints"""
    print("\n🧪 Testing NLWeb service...")
    
    # Test different localhost variations
    base_urls = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://0.0.0.0:8000"
    ]
    
    working_base_url = None
    
    # Find working base URL
    for base_url in base_urls:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(base_url)
                print(f"✅ {base_url} is accessible (Status: {response.status_code})")
                working_base_url = base_url
                break
        except Exception as e:
            print(f"❌ {base_url} failed: {type(e).__name__}")
    
    if not working_base_url:
        print("❌ No working base URL found")
        return False
    
    # Test the /ask endpoint
    print(f"\n🎯 Testing /ask endpoint at {working_base_url}...")
    
    try:
        params = {
            "query": "test search query",
            "site": "all",
            "model": "auto",
            "prev": "[]",
            "item_to_remember": "",
            "context_url": "",
            "streaming": "false"
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{working_base_url}/ask", params=params)
            
            print(f"✅ /ask endpoint works!")
            print(f"   Status: {response.status_code}")
            print(f"   Content-Type: {response.headers.get('content-type', 'unknown')}")
            print(f"   Response length: {len(response.text)} characters")
            
            # Try to parse JSON
            try:
                json_data = response.json()
                print(f"✅ Valid JSON response")
                if isinstance(json_data, dict):
                    print(f"   JSON keys: {list(json_data.keys())}")
                
                # Update the MCP server URL if needed
                if working_base_url != "http://localhost:8000":
                    print(f"\n💡 Update your MCP server to use: {working_base_url}/ask")
                    
            except Exception as json_err:
                print(f"⚠️  Response might not be JSON: {json_err}")
                print(f"   First 200 chars: {response.text[:200]}")
            
            return True
            
    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP error: {e.response.status_code}")
        print(f"   Error response: {e.response.text[:300]}")
        return False
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def show_nlweb_logs(process, duration=10):
    """Show NLWeb service logs for a few seconds"""
    if not process:
        return
        
    print(f"\n📋 Showing NLWeb logs for {duration} seconds...")
    print("=" * 50)
    
    start_time = time.time()
    while time.time() - start_time < duration:
        if process.poll() is not None:
            print("❌ Process terminated!")
            stdout, stderr = process.communicate()
            if stdout:
                print("STDOUT:", stdout)
            if stderr:
                print("STDERR:", stderr)
            break
            
        # Check for output (non-blocking)
        try:
            import select
            # This is more complex on Windows, so we'll just wait
            time.sleep(1)
        except:
            time.sleep(1)
    
    print("=" * 50)

async def main():
    print("NLWeb Service Manager")
    print("=" * 50)
    
    # Step 1: Kill any hanging processes
    print("1️⃣ Cleaning up existing processes...")
    kill_process_on_port(8000)
    
    # Step 2: Start the NLWeb service
    print("\n2️⃣ Starting NLWeb service...")
    process = start_nlweb_service()
    
    if not process:
        print("❌ Failed to start NLWeb service")
        return
    
    # Step 3: Show logs briefly
    show_nlweb_logs(process, 5)
    
    # Step 4: Test the service
    print("\n3️⃣ Testing the service...")
    success = await test_nlweb_endpoints()
    
    if success:
        print("\n🎉 SUCCESS! NLWeb service is running and responding correctly!")
        print("\nYour MCP server should now work. The service will keep running.")
        print("Press Ctrl+C to stop this script (the NLWeb service will continue running)")
        
        # Keep the script running so the service stays up
        try:
            while True:
                time.sleep(60)
                # Check if process is still alive
                if process.poll() is not None:
                    print("⚠️  NLWeb service stopped unexpectedly")
                    break
        except KeyboardInterrupt:
            print("\n🛑 Script stopped. NLWeb service is still running in the background.")
    else:
        print("\n❌ Service started but not responding correctly")
        print("Check the logs above for errors")
        
        # Kill the process since it's not working
        try:
            process.terminate()
            time.sleep(2)
            if process.poll() is None:
                process.kill()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(main())