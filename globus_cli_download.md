# Globus CLI Data Transfer Guide

Quick reference for transferring sequencing data using Globus CLI.

## Prerequisites

```bash
# Install Globus CLI (one-time)
mamba create -n globus globus-cli
mamba activate globus

# Authenticate (do this once or when session expires)
globus login
```

## 1. Find Shared Data

When someone shares data with you via Globus:

```bash
# List collections shared with you
globus endpoint search --filter-scope shared-with-me

# View collection details
globus gcs collection show <collection-id>

# Browse the shared data
globus ls <collection-id>:/
```

**Save the collection ID** - you'll need it as your source.

## 2. Check Your Destination Endpoint

### Option A: Use institutional endpoint (preferred)

```bash
# Search for UCSC endpoints
globus endpoint search "ucsc"

# Test access
globus ls <endpoint-id>:/

# If accessible, save the endpoint ID
```

### Option B: Set up Globus Connect Personal

#### For Linux servers:

```bash
# Download and extract (one-time setup)
cd ~
wget https://downloads.globus.org/globus-connect-personal/linux/stable/globusconnectpersonal-latest.tgz
tar xzf globusconnectpersonal-latest.tgz
cd globusconnectpersonal-*

# Setup (follow prompts to authenticate)
./globusconnectpersonal -setup

# Start in background with screen
screen -S globus
./globusconnectpersonal -start
# Press Ctrl+A, then D to detach

# Find your endpoint ID
globus endpoint search --filter-scope my-endpoints
```

**Configure Accessible Paths (Linux):**

By default, Globus Connect Personal only allows access to your home directory. To access other paths:

```bash
# Stop the endpoint
cd ~/globusconnectpersonal-*
./globusconnectpersonal -stop

# Edit the config file
nano ~/.globusonline/lta/config-paths
```

Add paths you need access to (one per line):
```
/private/groups/russelllab/,0,1
```

Format: `path,writable(0=yes,1=no),shareable`

Save and restart:
```bash
./globusconnectpersonal -start
```

#### For macOS (local machine or mounted drives):

**Installation:**

```bash
# Download the macOS version
cd ~/Downloads
curl -LO https://downloads.globus.org/globus-connect-personal/mac/stable/globusconnectpersonal-latest.dmg

# Open the DMG file
open globusconnectpersonal-latest.dmg
```

Then:
1. Drag "Globus Connect Personal" to your Applications folder
2. Open "Globus Connect Personal" from Applications (or use Spotlight: Cmd+Space, type "Globus")
3. Follow the setup wizard:
   - Sign in with your institutional account or Globus ID
   - Complete authentication in your web browser
   - Return to the app to finish setup

**Configure Accessible Paths (macOS):**

After installation and first launch:

1. Click the **Globus "g" icon** in your menu bar (top right of screen)
2. Select **"Preferences"** from the dropdown menu
3. Click the **"Access"** tab
4. Click the **"+"** (plus) button to add a new folder
5. Navigate to the folder you want to make accessible:
   - For home directory: `/Users/your-username/data/`
   - For external drives: `/Volumes/drive_name/path/`
   - For mounted NAS: `/Volumes/nas_name/path/`
   - Example: `/Volumes/sequencing_data/scRNAseq/PIPseq-primary_cells`
6. Select the folder and click **"Open"**
7. **Check "Writable"** if you want to transfer files TO this location (not just from it)
8. Click **"Save"** at the bottom of the Preferences window

**Verify it's running:**

- The Globus "g" icon should appear in your menu bar when running
- Click it and verify the status shows as connected

**Find your Mac endpoint ID:**
```bash
# From terminal with Globus CLI
mamba activate globus
globus endpoint search --filter-scope my-endpoints
```

Your Mac will appear with a name like "your-name's MacBook Pro" and an endpoint ID.

**Important notes:**
- Globus Connect Personal must be running to transfer files
- External drives and NAS must be mounted before starting transfers
- The app will start automatically on login (can be changed in Preferences > General)

## 3. Transfer Data

```bash
globus transfer <source-collection-id>:/<source-path> \
                <destination-endpoint-id>:/<destination-path> \
                --recursive \
                --label "Description of transfer"
```

### Transfer to Linux server:
```bash
globus transfer 6fbe3d98-aaa6-482c-9815-a718be94d267:/ \
                ee0b4b13-9e29-11f0-ae47-0affca67c55f:/private/groups/russelllab/jodie/sequencing_data/scRNAseq/ \
                --recursive \
                --label "RNA-seq transfer from Duke"
```

### Transfer to local Mac:
```bash
globus transfer 6fbe3d98-aaa6-482c-9815-a718be94d267:/ \
                ecac34b1-9e33-11f0-8dfe-0e1cc5cf4f03:/Users/username/data/ \
                --recursive \
                --label "RNA-seq to local Mac"
# Hint: use 'caffeinate' command in another terminal tab to prevent computer from timing out
```

### Transfer to external drive or mounted NAS:
```bash
# Make sure the drive/NAS is mounted first!
globus transfer 6fbe3d98-aaa6-482c-9815-a718be94d267:/ \
                ecac34b1-9e33-11f0-8dfe-0e1cc5cf4f03:/Volumes/sequencing_data/scRNAseq/PIPseq-primary_cells/ \
                --recursive \
                --label "RNA-seq to NAS"
```

**Important:** For external drives and NAS, ensure:
- The drive is mounted before starting transfer
- You've added the path in Globus Connect Personal (Preferences > Access)
- Globus Connect Personal is running

The transfer runs server-side and continues even if you disconnect.

## 4. Monitor Transfer

```bash
# List all your transfers
globus task list

# Check specific transfer status
globus task show <task-id>

# View transfer events
globus task event-list <task-id> --limit 10

# Cancel a transfer if needed
globus task cancel <task-id>
```

You'll receive an email when the transfer completes.

## 5. Verify Transfer

```bash
# Check files arrived
ls -lh /path/to/destination/

# Verify checksums using provided .md5 file
cd /path/to/destination/
md5sum -c Jacobs_11177_250926A9.md5
```

This will show "OK" for each file if checksums match:
```
Dsim-Merrill23-1_S67_L003_R1_001.fastq.gz: OK
Dsim-Merrill23-1_S67_L003_R2_001.fastq.gz: OK
...
```

If you need to generate checksums (no provided .md5 file):
```bash
md5sum *.fastq.gz > computed.md5
```

## Troubleshooting

**Endpoint is non-functional:**
- Try alternative institutional endpoints
- Set up Globus Connect Personal

**Permission denied:**
- Verify you have write access to destination path: `ls -ld /path/to/destination`
- Add the path to Globus Connect Personal config:
  ```bash
  cd ~/globusconnectpersonal-*
  ./globusconnectpersonal -stop
  nano ~/.globusonline/lta/config-paths
  # Add: /path/to/directory/,0,1
  ./globusconnectpersonal -start
  ```
- Check endpoint is active: `./globusconnectpersonal -status`

**Transfer stuck:**
- Check task status: `globus task show <task-id>`
- Ensure Globus Connect Personal is still running (if using it)
- Reattach to screen: `screen -r globus`

## Keeping Globus Connect Personal Running

If using your own endpoint, keep it running:

```bash
# Reattach to screen session
screen -r globus

# Check status
cd ~/globusconnectpersonal-*
./globusconnectpersonal -status

# Restart if needed
./globusconnectpersonal -start
```

### Restarting Globus Connect Personal

```bash
# Navigate to installation directory
cd ~/globusconnectpersonal-*

# Stop the endpoint
./globusconnectpersonal -stop

# Start it again
./globusconnectpersonal -start

# Or run in background
./globusconnectpersonal -start &

# Verify it's running
./globusconnectpersonal -status
```

**If running in screen session:**
```bash
# List screen sessions
screen -ls

# Reattach to globus session
screen -r globus

# Inside screen, restart
cd ~/globusconnectpersonal-*
./globusconnectpersonal -stop
./globusconnectpersonal -start

# Detach with Ctrl+A, then D
```

## Quick Reference

| Task | Command |
|------|---------|
| Find shared data | `globus endpoint search --filter-scope shared-with-me` |
| Browse collection | `globus ls <collection-id>:/` |
| Find your endpoints | `globus endpoint search --filter-scope my-endpoints` |
| Start transfer | `globus transfer <source>:<path> <dest>:<path> --recursive` |
| List transfers | `globus task list` |
| Check transfer | `globus task show <task-id>` |
