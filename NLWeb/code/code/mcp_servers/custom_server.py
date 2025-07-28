from fastmcp import FastMCP, Context
from fastapi import HTTPException
import httpx
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

mcp = FastMCP(name="Your Custom MCP Server")

NLWEB_ASK_URL = "http://localhost:8000/ask"

@mcp.tool(name="get_job_status", description="Get status of a job application by ID")
async def get_job_status(ctx: Context, application_id: str) -> dict:
    # Replace with real logic
    status = query_database(application_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return {"application_id": application_id, "status": status}

def query_database(application_id: str):
    mock_db = {
        "app123": "Under Review",
        "app456": "Interview Scheduled",
        "app789": "Rejected",
    }
    return mock_db.get(application_id)

@mcp.tool(name="search_jobs", description="Search job postings via NLWeb")
async def search_jobs(ctx: Context, query: str, site: str = "all") -> dict:
    logger.info(f"Starting job search with query: '{query}', site: '{site}'")
    
    try:
        params = {
            "query": query,
            "site": site,
            "model": "auto",
            "prev": "[]",
            "item_to_remember": "",
            "context_url": "",
            "streaming": "false"
        }
        
        logger.info(f"Making request to: {NLWEB_ASK_URL}")
        logger.info(f"Request params: {params}")
        
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                logger.info("Sending HTTP request...")
                response = await client.get(NLWEB_ASK_URL, params=params)
                
                logger.info(f"Response status: {response.status_code}")
                logger.info(f"Response headers: {dict(response.headers)}")
                
                response.raise_for_status()
                
                # Log raw response content
                raw_content = response.text
                logger.info(f"Raw response content (first 500 chars): {raw_content[:500]}")
                
                try:
                    data = response.json()
                    logger.info(f"Parsed JSON keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                except Exception as json_error:
                    logger.error(f"JSON parsing error: {json_error}")
                    return {
                        "error": "Invalid JSON response from NLWeb",
                        "raw_response": raw_content[:1000],
                        "results": [],
                        "count": 0
                    }
                
            except httpx.ConnectError as e:
                logger.error(f"Connection error: {e}")
                return {
                    "error": f"Cannot connect to NLWeb service at {NLWEB_ASK_URL}. Is the service running?",
                    "details": str(e),
                    "results": [],
                    "count": 0
                }
            except httpx.TimeoutException as e:
                logger.error(f"Timeout error: {e}")
                return {
                    "error": "Request to NLWeb service timed out",
                    "details": str(e),
                    "results": [],
                    "count": 0
                }
            except httpx.RequestError as e:
                logger.error(f"Request error: {e}")
                return {
                    "error": f"Request error when contacting NLWeb: {type(e).__name__}",
                    "details": str(e),
                    "results": [],
                    "count": 0
                }
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP status error: {e}")
                detail = f"HTTP {e.response.status_code}"
                if e.response is not None:
                    try:
                        response_text = e.response.text
                        logger.error(f"Error response content: {response_text}")
                        detail += f" - Response: {response_text[:500]}"
                    except Exception:
                        pass
                return {
                    "error": f"NLWeb service returned error: {e.response.status_code}",
                    "details": detail,
                    "results": [],
                    "count": 0
                }

        # Parse results safely
        logger.info("Parsing job results...")
        jobs = []
        
        # Check different possible response structures
        items = None
        if isinstance(data, dict):
            # Try common response keys
            for key in ["items", "results", "data", "jobs", "response"]:
                if key in data:
                    items = data[key]
                    logger.info(f"Found items under key '{key}': {len(items) if isinstance(items, list) else 'not a list'}")
                    break
        
        if items is None:
            logger.warning(f"No items found in response. Full response structure: {data}")
            return {
                "warning": "No items found in NLWeb response",
                "raw_response": data,
                "results": [],
                "count": 0
            }
        
        if not isinstance(items, list):
            logger.warning(f"Items is not a list: {type(items)}")
            return {
                "warning": "Items field is not a list",
                "raw_response": data,
                "results": [],
                "count": 0
            }
        
        for i, item in enumerate(items):
            logger.debug(f"Processing item {i}: {item}")
            if not isinstance(item, dict):
                logger.warning(f"Item {i} is not a dictionary: {type(item)}")
                continue
                
            job = {
                "title": item.get("title", "No title"),
                "description": item.get("description", "No description"),
                "location": item.get("jobLocation", {}).get("address", {}).get("addressLocality", "Unknown"),
                "datePosted": item.get("datePosted", "Unknown"),
                "raw_item": item  # Include raw item for debugging
            }
            jobs.append(job)

        logger.info(f"Successfully parsed {len(jobs)} jobs")
        return {"results": jobs, "count": len(jobs)}
    
    except Exception as e:
        logger.error(f"Unexpected error in search_jobs: {e}", exc_info=True)
        return {
            "error": f"Unexpected error: {type(e).__name__}",
            "details": str(e),
            "results": [],
            "count": 0
        }

# Add a simple health check tool
@mcp.tool(name="health_check", description="Check if NLWeb service is accessible")
async def health_check(ctx: Context) -> dict:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Try a simple request to check if service is up
            response = await client.get("http://localhost:8000/", follow_redirects=True)
            return {
                "status": "accessible",
                "status_code": response.status_code,
                "service_url": "http://localhost:8000/"
            }
    except httpx.ConnectError:
        return {
            "status": "connection_failed",
            "error": "Cannot connect to http://localhost:8000/",
            "suggestion": "Make sure NLWeb service is running on port 8000"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

if __name__ == "__main__":
    mcp.run()  # runs server on default transport and port (stdio or SSE)