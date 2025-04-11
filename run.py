import os
import sys
import subprocess
import time
import webbrowser
import signal
import logging
from threading import Thread
import requests # Add this import

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global variables to track processes
backend_process = None
frontend_process = None

# Function to start the FastAPI backend
def start_backend():
    global backend_process
    try:
        logger.info("Starting FastAPI backend...")
        # Check if required packages are installed
        try:
            import retrying
        except ImportError:
            logger.error("Required package 'retrying' is not installed. Installing now...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "retrying"])
            logger.info("Package 'retrying' installed successfully.")
            
        # Use uvicorn to run the FastAPI app
        # Use PIPE for stdout/stderr to capture logs if needed, but primarily rely on uvicorn's logging
        backend_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "api:app", "--host", "127.0.0.1", "--port", "8000"],
            stdout=sys.stdout, # Redirect stdout to main process stdout
            stderr=sys.stderr  # Redirect stderr to main process stderr
        )

        # Wait for backend to be ready
        logger.info("Waiting for backend to become ready...")
        backend_ready = False
        start_time = time.time()
        timeout = 60  # 60 seconds timeout
        retry_interval = 2  # seconds between retries
        max_retries = 5  # maximum number of retries for each endpoint

        # First check the root endpoint to ensure the server is running
        root_ready = False
        retry_count = 0
        
        while not root_ready and time.time() - start_time < timeout and retry_count < max_retries:
            # Check if process has terminated unexpectedly
            if backend_process.poll() is not None:
                logger.error("Backend process terminated unexpectedly during startup.")
                return False # Indicate failure

            # Try to connect to the backend root endpoint
            try:
                response = requests.get("http://127.0.0.1:8000/", timeout=2)
                if response.status_code == 200:
                    root_ready = True
                    logger.info("Backend root endpoint is accessible.")
                else:
                    logger.debug(f"Backend root check: Status code {response.status_code}")
                    retry_count += 1
            except requests.exceptions.ConnectionError:
                logger.debug("Backend root check: Connection refused, retrying...")
                retry_count += 1
            except requests.exceptions.Timeout:
                logger.debug("Backend root check: Connection timed out, retrying...")
                retry_count += 1
            except Exception as e:
                logger.warning(f"Backend root check: Encountered error - {e}, retrying...")
                retry_count += 1

            if not root_ready:
                time.sleep(retry_interval)
        
        if not root_ready:
            logger.error("Backend root endpoint did not become accessible within the timeout period.")
            return False
        
        # Now check the recent_queries endpoint to ensure the API is fully initialized
        # This is the endpoint that the frontend tries to access on startup
        retry_count = 0
        while not backend_ready and time.time() - start_time < timeout and retry_count < max_retries:
            try:
                response = requests.get("http://127.0.0.1:8000/recent_queries", timeout=2)
                if response.status_code == 200:
                    backend_ready = True
                    logger.info("Backend API is fully initialized and ready to accept connections.")
                else:
                    logger.debug(f"Backend API check: Status code {response.status_code}")
                    retry_count += 1
            except requests.exceptions.ConnectionError:
                logger.debug("Backend API check: Connection refused, retrying...")
                retry_count += 1
            except requests.exceptions.Timeout:
                logger.debug("Backend API check: Connection timed out, retrying...")
                retry_count += 1
            except Exception as e:
                logger.warning(f"Backend API check: Encountered error - {e}, retrying...")
                retry_count += 1

            if not backend_ready:
                time.sleep(retry_interval)

        if not backend_ready:
            logger.error("Backend API did not fully initialize within the timeout period.")
            return False # Indicate failure

        logger.info("Backend started successfully and is fully operational.")
        return True # Indicate success

    except Exception as e:
        logger.error(f"Error starting backend: {str(e)}")
        return False # Indicate failure

# Function to start the Streamlit frontend
def start_frontend():
    global frontend_process
    try:
        logger.info("Starting Streamlit frontend...")

        # Start a separate thread to monitor frontend output and open browser
        # (This part is less critical than the backend readiness)
        def monitor_and_open():
            url_opened = False
            if frontend_process:
                # Use readline directly from stderr as Streamlit often prints the URL there
                for line in iter(frontend_process.stderr.readline, ''):
                    if line:
                        logger.info(f"Frontend: {line.strip()}")
                        # Check if Streamlit provides the local URL
                        if not url_opened and ("Network URL:" in line or "Local URL:" in line) :
                             # Extract URL robustly
                            try:
                                url = line.split("URL:")[1].strip()
                                if url.startswith(" http"): # Handle potential leading space
                                     url = url.strip()
                                logger.info(f"Attempting to open browser at {url}")
                                webbrowser.open(url)
                                url_opened = True
                            except Exception as e:
                                logger.error(f"Failed to parse or open URL from line '{line.strip()}': {e}")


        # Use streamlit to run the frontend
        frontend_process = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "main_ui.py"],
            stdout=sys.stdout, # Redirect stdout
            stderr=subprocess.PIPE, # Capture stderr to find URL
            text=True,
            bufsize=1  # Line buffered
        )
        logger.info("Streamlit process launched.")

        # Start the output monitoring/browser opening thread
        output_thread = Thread(target=monitor_and_open)
        output_thread.daemon = True
        output_thread.start()

        # Wait for the frontend process to complete (it usually runs until stopped)
        frontend_process.wait()
        logger.info("Streamlit frontend process finished.")

    except Exception as e:
        logger.error(f"Error starting frontend: {str(e)}")
        # If frontend fails, we might want to stop the backend too
        if backend_process:
             backend_process.terminate()
        sys.exit(1)

# Function to clean up processes on exit
def cleanup(signum=None, frame=None):
    logger.info("Shutting down...")

    # Terminate frontend first if it's running
    if frontend_process and frontend_process.poll() is None:
        logger.info("Terminating frontend process...")
        frontend_process.terminate()
        try:
            frontend_process.wait(timeout=5) # Wait briefly for termination
        except subprocess.TimeoutExpired:
            logger.warning("Frontend process did not terminate gracefully, killing.")
            frontend_process.kill()

    # Terminate backend
    if backend_process and backend_process.poll() is None:
        logger.info("Terminating backend process...")
        backend_process.terminate()
        try:
             backend_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
             logger.warning("Backend process did not terminate gracefully, killing.")
             backend_process.kill()


    logger.info("Cleanup complete")
    sys.exit(0)

# Register signal handlers for graceful shutdown
signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

# Check if data directory exists, create if not
if not os.path.exists('data'):
    os.makedirs('data')
    logger.info("Created data directory")

# Check if .env file exists, warn if not
if not os.path.exists('.env'):
    logger.warning(".env file not found. Creating from example...")
    if os.path.exists('.env.example'):
        try:
            with open('.env.example', 'r') as example_file, open('.env', 'w') as env_file:
                env_file.write(example_file.read())
            logger.info(".env file created from example. Please edit it with your actual API token(s).")
        except Exception as e:
            logger.error(f"Failed to create .env from example: {e}")
    else:
        logger.error(".env.example file not found. Please create a .env file with necessary API tokens (e.g., HUGGINGFACEHUB_API_TOKEN).")


# Main function to run the application
def main():
    try:
        # Start backend *sequentially* and wait for it to be ready
        backend_ok = start_backend()

        if backend_ok:
            # Add a small delay to ensure backend is fully initialized
            logger.info("Adding a short delay to ensure backend is fully initialized...")
            time.sleep(3)
            
            # Only start frontend if backend started successfully
            start_frontend()
        else:
            logger.error("Backend failed to start. Exiting.")
            cleanup() # Ensure cleanup happens even if backend fails

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        cleanup()
    except Exception as e:
        logger.error(f"Unexpected error in main execution: {str(e)}")
        cleanup()

if __name__ == "__main__":
    print("Starting Supplement Price Comparison Agent...")
    print("Backend logs will appear below. Frontend will open in a browser when ready.")
    print("Press Ctrl+C to stop the application")
    main()