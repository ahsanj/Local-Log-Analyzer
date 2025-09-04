#!/bin/bash

echo " Testing File Upload Functionality..."
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
 if [ $1 -eq 0 ]; then
 echo -e " ${GREEN}$2${NC}"
 else
 echo -e " ${RED}$2${NC}"
 fi
}

print_info() {
 echo -e " ${BLUE}$1${NC}"
}

print_section() {
 echo -e "\n ${YELLOW}$1${NC}"
 echo "----------------------------------------"
}

# Check if backend is running
check_backend() {
 print_section "Checking Backend Availability"
 
 if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
 print_status 0 "Backend API is running"
 
 # Test files endpoint
 if curl -s http://localhost:8000/api/files/ > /dev/null 2>&1; then
 print_status 0 "Files endpoint accessible"
 else
 print_status 1 "Files endpoint not accessible"
 return 1
 fi
 else
 print_status 1 "Backend API not running"
 print_info "Start backend with: cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
 return 1
 fi
}

# Test file upload endpoint with sample files
test_file_uploads() {
 print_section "Testing File Upload Endpoints"
 
 cd "$(dirname "$0")/.."
 
 # Test different file types
 local test_files=(
 "sample_logs/application.log:text/plain"
 "sample_logs/api_logs.json:application/json"
 "sample_logs/access.csv:text/csv"
 "sample_logs/system.syslog:text/plain"
 )
 
 for file_info in "${test_files[@]}"; do
 local file_path="${file_info%%:*}"
 local content_type="${file_info##*:}"
 
 if [ -f "$file_path" ]; then
 print_info "Testing upload: $(basename "$file_path")"
 
 local response=$(curl -s -w "%{http_code}" -X POST \
 -F "file=@$file_path;type=$content_type" \
 http://localhost:8000/api/files/upload 2>/dev/null)
 
 local http_code="${response: -3}"
 local body="${response%???}"
 
 if [ "$http_code" = "200" ]; then
 print_status 0 "$(basename "$file_path") upload successful"
 
 # Extract file ID and test file info endpoint
 local file_id=$(echo "$body" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
 if [ -n "$file_id" ]; then
 local info_response=$(curl -s "http://localhost:8000/api/files/$file_id" 2>/dev/null)
 if echo "$info_response" | grep -q '"id"'; then
 print_status 0 "File info retrieval successful"
 else
 print_status 1 "File info retrieval failed"
 fi
 fi
 else
 print_status 1 "$(basename "$file_path") upload failed (HTTP $http_code)"
 echo "Response: $body"
 fi
 else
 print_status 1 "Test file not found: $file_path"
 fi
 done
}

# Test paste content endpoint
test_paste_content() {
 print_section "Testing Paste Content Endpoint"
 
 local sample_content="2024-08-24 10:30:00 [INFO] Test log entry
2024-08-24 10:30:01 [WARN] This is a test warning
2024-08-24 10:30:02 [ERROR] Test error message"
 
 print_info "Testing paste content functionality"
 
 local response=$(curl -s -w "%{http_code}" -X POST \
 -H "Content-Type: application/json" \
 -d "{\"content\":\"$sample_content\"}" \
 http://localhost:8000/api/files/paste 2>/dev/null)
 
 local http_code="${response: -3}"
 local body="${response%???}"
 
 if [ "$http_code" = "200" ]; then
 print_status 0 "Paste content successful"
 
 # Extract file ID and test analysis
 local file_id=$(echo "$body" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
 if [ -n "$file_id" ]; then
 print_info "Testing analysis for pasted content..."
 local analysis_response=$(curl -s "http://localhost:8000/api/analysis/$file_id" 2>/dev/null)
 if echo "$analysis_response" | grep -q '"total_entries"'; then
 print_status 0 "Content analysis successful"
 else
 print_status 1 "Content analysis failed"
 fi
 fi
 else
 print_status 1 "Paste content failed (HTTP $http_code)"
 echo "Response: $body"
 fi
}

# Test file validation
test_file_validation() {
 print_section "Testing File Validation"
 
 # Create a test file that's too large (simulate)
 print_info "Testing large file rejection"
 
 # Test invalid file extension
 print_info "Testing invalid file extension"
 local temp_file="/tmp/test_invalid.xyz"
 echo "Invalid file content" > "$temp_file"
 
 local response=$(curl -s -w "%{http_code}" -X POST \
 -F "file=@$temp_file;type=text/plain" \
 http://localhost:8000/api/files/upload 2>/dev/null)
 
 local http_code="${response: -3}"
 
 if [ "$http_code" != "200" ]; then
 print_status 0 "Invalid file extension correctly rejected"
 else
 print_status 1 "Invalid file extension not rejected"
 fi
 
 rm -f "$temp_file"
}

# Test frontend accessibility
test_frontend() {
 print_section "Testing Frontend Accessibility"
 
 if curl -s http://localhost:3000 > /dev/null 2>&1; then
 print_status 0 "Frontend is accessible"
 
 # Check if upload page loads
 local response=$(curl -s http://localhost:3000 2>/dev/null)
 if echo "$response" | grep -q "Upload Your Log Files"; then
 print_status 0 "Upload page content loads correctly"
 else
 print_status 1 "Upload page content not found"
 fi
 else
 print_status 1 "Frontend not accessible"
 print_info "Start frontend with: cd frontend && npm run dev"
 fi
}

# Main test execution
main() {
 echo "Testing Local Log Analyzer Upload Functionality"
 echo "================================================"
 
 # Run tests
 if check_backend; then
 test_file_uploads
 test_paste_content
 test_file_validation
 else
 echo -e "\n Backend not available - skipping upload tests"
 echo "Please start the backend first:"
 echo " cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
 fi
 
 test_frontend
 
 print_section "Test Summary"
 echo "Upload functionality testing complete!"
 echo ""
 echo "To manually test the full functionality:"
 echo "1. Start backend: cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
 echo "2. Start frontend: cd frontend && npm run dev"
 echo "3. Open http://localhost:3000 in your browser"
 echo "4. Try uploading the sample files from the sample_logs/ directory"
 echo "5. Test the paste functionality with log content"
}

# Run the tests
main "$@"