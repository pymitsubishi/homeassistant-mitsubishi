#!/bin/bash

# Build and Deploy Script for Home Assistant Mitsubishi Integration
# Supports both development (local pymitsubishi) and production (PyPI) modes

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
HA_SERVER="192.168.1.162"
HA_USER="ashhopkins"
SSHPASS_FILE="../.sshpass"
PYMITSUBISHI_PATH="../pymitsubishi/pymitsubishi"  # Path to the pymitsubishi Python package
COMPONENT_PATH="custom_components/mitsubishi"

# Parse command line arguments
MODE="production"  # Default to production mode
SKIP_RESTART=false
SKIP_DEPLOY=false

function usage() {
    echo -e "${BLUE}Usage: $0 [OPTIONS]${NC}"
    echo ""
    echo "Options:"
    echo "  --dev, -d          Use local pymitsubishi library (development mode)"
    echo "  --prod, -p         Use PyPI pymitsubishi library (production mode) [default]"
    echo "  --local-only, -l   Build package only, don't deploy to server"
    echo "  --no-restart, -n   Deploy but don't restart Home Assistant"
    echo "  --help, -h         Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                 # Production build and deploy with restart"
    echo "  $0 --dev           # Development build with local pymitsubishi"
    echo "  $0 --prod -n       # Production deploy without restart"
    echo "  $0 --dev -l        # Development build only (no deploy)"
    exit 0
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --dev|-d)
            MODE="dev"
            shift
            ;;
        --prod|-p)
            MODE="production"
            shift
            ;;
        --local-only|-l)
            SKIP_DEPLOY=true
            shift
            ;;
        --no-restart|-n)
            SKIP_RESTART=true
            shift
            ;;
        --help|-h)
            usage
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            usage
            ;;
    esac
done

# Set package name based on mode
if [ "$MODE" = "dev" ]; then
    PACKAGE_NAME="mitsubishi-integration-dev.tar.gz"
    echo -e "${MAGENTA}=== Home Assistant Mitsubishi Integration - DEVELOPMENT Build ===${NC}"
    echo -e "${YELLOW}This will bundle the local pymitsubishi library for testing${NC}"
else
    PACKAGE_NAME="mitsubishi-integration.tar.gz"
    echo -e "${BLUE}=== Home Assistant Mitsubishi Integration - PRODUCTION Build ===${NC}"
    echo -e "${GREEN}This will use the PyPI version of pymitsubishi${NC}"
fi
echo ""

# Check if we're in the right directory
if [ ! -d "$COMPONENT_PATH" ]; then
    echo -e "${RED}Error: $COMPONENT_PATH directory not found!${NC}"
    echo "Please run this script from the homeassistant-mitsubishi directory."
    exit 1
fi

# In dev mode, check if pymitsubishi source exists
if [ "$MODE" = "dev" ]; then
    if [ ! -d "$PYMITSUBISHI_PATH" ]; then
        echo -e "${RED}Error: pymitsubishi source not found at $PYMITSUBISHI_PATH${NC}"
        echo "Development mode requires the local pymitsubishi library."
        exit 1
    fi
fi

# Check if sshpass file exists (only if deploying)
if [ "$SKIP_DEPLOY" = false ]; then
    if [ ! -f "$SSHPASS_FILE" ]; then
        echo -e "${RED}Error: SSH password file not found at $SSHPASS_FILE${NC}"
        echo "Deployment requires the SSH password file."
        exit 1
    fi
fi

# Prepare the integration based on mode
if [ "$MODE" = "dev" ]; then
    # Development mode: Bundle local pymitsubishi

    # Step 1: Bundle the local pymitsubishi library
    echo -e "${YELLOW}[1/3] Bundling local pymitsubishi library...${NC}"

    # Remove old pymitsubishi directory if it exists
    if [ -d "$COMPONENT_PATH/pymitsubishi" ]; then
        echo "  Removing old bundled library..."
        rm -rf "$COMPONENT_PATH/pymitsubishi"
    fi

    # Create the pymitsubishi directory in the component
    mkdir -p "$COMPONENT_PATH/pymitsubishi"

    # Copy only the Python files from the pymitsubishi package
    echo "  Copying pymitsubishi Python files from $PYMITSUBISHI_PATH..."
    cp "$PYMITSUBISHI_PATH"/*.py "$COMPONENT_PATH/pymitsubishi/"

    echo "  Copied $(ls -1 $COMPONENT_PATH/pymitsubishi/*.py | wc -l) Python files"
    echo -e "${GREEN}✓ Library bundled${NC}"

    # Step 2: Modify manifest.json for dev mode
    echo -e "${YELLOW}[2/3] Modifying manifest.json for development mode...${NC}"

    MANIFEST_FILE="$COMPONENT_PATH/manifest.json"
    MANIFEST_BACKUP="$COMPONENT_PATH/manifest.json.backup"

    # Create backup if it doesn't exist
    if [ ! -f "$MANIFEST_BACKUP" ]; then
        cp "$MANIFEST_FILE" "$MANIFEST_BACKUP"
        echo "  Created backup: manifest.json.backup"
    fi

    # Remove pymitsubishi requirement for dev mode
    python3 << EOF
import json
import sys

manifest_file = "$MANIFEST_FILE"

try:
    with open(manifest_file, 'r') as f:
        manifest = json.load(f)

    # Remove pymitsubishi from requirements
    original_reqs = manifest.get('requirements', [])
    manifest['requirements'] = [req for req in original_reqs if 'pymitsubishi' not in req.lower()]

    # Add a comment field to indicate dev mode
    manifest['_dev_mode'] = "Using bundled pymitsubishi library"

    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"  Modified manifest.json (removed {len(original_reqs) - len(manifest['requirements'])} pymitsubishi requirement(s))")
except Exception as e:
    print(f"Error modifying manifest.json: {e}", file=sys.stderr)
    sys.exit(1)
EOF

    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Failed to modify manifest.json${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ manifest.json modified for development${NC}"

    # Step 3: Update imports to use bundled library
    echo -e "${YELLOW}[3/3] Updating imports to use bundled library...${NC}"

    IMPORT_COUNT=0
    for py_file in $(find "$COMPONENT_PATH" -name "*.py" -not -path "*/pymitsubishi/*"); do
        if grep -q "from pymitsubishi" "$py_file" || grep -q "import pymitsubishi" "$py_file"; then
            if ! grep -q "from \.pymitsubishi" "$py_file"; then
                echo "  Updating imports in $(basename $py_file)..."
                sed -i '' 's/from pymitsubishi/from .pymitsubishi/g' "$py_file"
                sed -i '' 's/import pymitsubishi/from . import pymitsubishi/g' "$py_file"
                IMPORT_COUNT=$((IMPORT_COUNT + 1))
            fi
        fi
    done

    if [ $IMPORT_COUNT -gt 0 ]; then
        echo -e "${GREEN}✓ Updated imports in $IMPORT_COUNT file(s)${NC}"
    else
        echo -e "${GREEN}✓ All imports already using bundled library${NC}"
    fi

else
    # Production mode: Ensure clean state

    # Step 1: Clean up any dev mode artifacts
    echo -e "${YELLOW}[1/2] Preparing production build...${NC}"

    # Remove bundled pymitsubishi if it exists
    if [ -d "$COMPONENT_PATH/pymitsubishi" ]; then
        echo "  Removing bundled pymitsubishi library..."
        rm -rf "$COMPONENT_PATH/pymitsubishi"
        echo -e "${GREEN}✓ Removed bundled library${NC}"
    fi

    # Step 2: Restore production manifest.json
    echo -e "${YELLOW}[2/2] Ensuring manifest.json is in production state...${NC}"

    MANIFEST_FILE="$COMPONENT_PATH/manifest.json"
    MANIFEST_BACKUP="$COMPONENT_PATH/manifest.json.backup"

    # If backup exists, restore it
    if [ -f "$MANIFEST_BACKUP" ]; then
        cp "$MANIFEST_BACKUP" "$MANIFEST_FILE"
        echo "  Restored manifest.json from backup"
    fi

    # Ensure pymitsubishi requirement is present
    python3 << EOF
import json
import sys

manifest_file = "$MANIFEST_FILE"

try:
    with open(manifest_file, 'r') as f:
        manifest = json.load(f)

    # Ensure pymitsubishi is in requirements
    requirements = manifest.get('requirements', [])
    has_pymitsubishi = any('pymitsubishi' in req.lower() for req in requirements)

    if not has_pymitsubishi:
        requirements.append('pymitsubishi>=0.2.0')
        manifest['requirements'] = requirements
        print("  Added pymitsubishi>=0.2.0 to requirements")

    # Remove dev mode marker if present
    if '_dev_mode' in manifest:
        del manifest['_dev_mode']
        print("  Removed dev mode marker")

    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)

    print("  manifest.json ready for production")
except Exception as e:
    print(f"Error modifying manifest.json: {e}", file=sys.stderr)
    sys.exit(1)
EOF

    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Failed to prepare manifest.json${NC}"
        exit 1
    fi

    # Restore normal imports
    for py_file in $(find "$COMPONENT_PATH" -name "*.py"); do
        if grep -q "from \.pymitsubishi" "$py_file"; then
            echo "  Restoring imports in $(basename $py_file)..."
            sed -i '' 's/from \.pymitsubishi/from pymitsubishi/g' "$py_file"
            sed -i '' 's/from \. import pymitsubishi/import pymitsubishi/g' "$py_file"
        fi
    done

    echo -e "${GREEN}✓ Production build prepared${NC}"
fi

# Build the package
echo ""
echo -e "${YELLOW}Building integration package...${NC}"
tar -czf "$PACKAGE_NAME" "$COMPONENT_PATH"
echo -e "${GREEN}✓ Package built: $PACKAGE_NAME${NC}"

# Deploy if not skipped
if [ "$SKIP_DEPLOY" = false ]; then
    echo ""
    echo -e "${YELLOW}Deploying to Home Assistant server ($HA_SERVER)...${NC}"
    cat "$PACKAGE_NAME" | sshpass -f "$SSHPASS_FILE" ssh "$HA_USER@$HA_SERVER" "sudo tar -xzf - -C /config/"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Integration deployed successfully${NC}"
    else
        echo -e "${RED}✗ Deployment failed${NC}"
        exit 1
    fi

    # Restart if not skipped
    if [ "$SKIP_RESTART" = false ]; then
        echo ""
        echo -e "${YELLOW}Restarting Home Assistant...${NC}"
        sshpass -f "$SSHPASS_FILE" ssh "$HA_USER@$HA_SERVER" "sudo docker restart homeassistant"
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Home Assistant restarting${NC}"

            # Wait for restart
            echo -e "${YELLOW}Waiting for Home Assistant to start (30 seconds)...${NC}"
            sleep 30

            # Check integration status
            echo ""
            echo -e "${YELLOW}Checking integration status...${NC}"
            sshpass -f "$SSHPASS_FILE" ssh "$HA_USER@$HA_SERVER" "sudo grep -i mitsubishi /config/home-assistant.log | tail -10"
        else
            echo -e "${RED}✗ Failed to restart Home Assistant${NC}"
            exit 1
        fi
    else
        echo ""
        echo -e "${YELLOW}Skipping Home Assistant restart (--no-restart flag)${NC}"
    fi
else
    echo ""
    echo -e "${YELLOW}Skipping deployment (--local-only flag)${NC}"
fi

# Summary
echo ""
if [ "$MODE" = "dev" ]; then
    echo -e "${GREEN}=== DEVELOPMENT Build Complete ===${NC}"
    echo -e "${MAGENTA}Using bundled pymitsubishi library from: $PYMITSUBISHI_PATH${NC}"
else
    echo -e "${GREEN}=== PRODUCTION Build Complete ===${NC}"
    echo -e "${BLUE}Using PyPI pymitsubishi (version >=0.2.0)${NC}"
fi

if [ "$SKIP_DEPLOY" = false ]; then
    echo ""
    echo -e "${GREEN}Deployment Status:${NC}"
    echo "  • Package: $PACKAGE_NAME"
    echo "  • Server: $HA_SERVER"
    echo "  • Deployed: ✓"
    if [ "$SKIP_RESTART" = false ]; then
        echo "  • Restarted: ✓"
    else
        echo "  • Restarted: Skipped"
    fi

    echo ""
    echo -e "${YELLOW}Useful commands:${NC}"
    echo "  Monitor logs:     sshpass -f $SSHPASS_FILE ssh $HA_USER@$HA_SERVER \"sudo tail -f /config/home-assistant.log | grep -i mitsubishi\""
    echo "  Check status:     sshpass -f $SSHPASS_FILE ssh $HA_USER@$HA_SERVER \"sudo grep -i mitsubishi /config/home-assistant.log | tail -20\""
    if [ "$SKIP_RESTART" = true ]; then
        echo "  Restart HA:       sshpass -f $SSHPASS_FILE ssh $HA_USER@$HA_SERVER \"sudo docker restart homeassistant\""
    fi
else
    echo ""
    echo -e "${YELLOW}Package created: $PACKAGE_NAME${NC}"
    echo "To deploy manually, run:"
    echo "  cat $PACKAGE_NAME | sshpass -f $SSHPASS_FILE ssh $HA_USER@$HA_SERVER \"sudo tar -xzf - -C /config/\""
    echo "  sshpass -f $SSHPASS_FILE ssh $HA_USER@$HA_SERVER \"sudo docker restart homeassistant\""
fi

if [ "$MODE" = "dev" ]; then
    echo ""
    echo -e "${YELLOW}To switch to production mode, run:${NC}"
    echo "  $0 --prod"
fi
