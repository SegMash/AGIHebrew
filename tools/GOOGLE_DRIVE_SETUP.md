# Google Drive API Setup Guide

## Prerequisites
1. Install required packages:
   ```
   pip install -r requirements_drive.txt
   ```

## Google Drive API Setup

### Step 1: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Name it something like "Hebrew Translation Project"

### Step 2: Enable Google Drive API
1. In the Google Cloud Console, go to "APIs & Services" > "Library"
2. Search for "Google Drive API"
3. Click on it and press "Enable"

### Step 3: Create Credentials
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. If prompted, configure the consent screen:
   - User Type: External (unless you have Google Workspace)
   - App name: "Hebrew Translation Tool"
   - User support email: your email
   - Authorized domains: can leave empty for testing
   - Scopes: Add ../auth/drive (Google Drive access)
4. For Application type, choose "Desktop application"
5. Name it "Hebrew Translation Desktop"
6. Click "Create"

### Step 4: Download Credentials
1. After creating, click the download icon next to your credential
2. Save the JSON file as `client_secrets.json` in the `tools` directory
3. The file should look like:
   ```json
   {
     "installed": {
       "client_id": "your-client-id.googleusercontent.com",
       "client_secret": "your-secret",
       "auth_uri": "https://accounts.google.com/o/oauth2/auth",
       "token_uri": "https://oauth2.googleapis.com/token",
       ...
     }
   }
   ```

### Step 5: First Run Authentication
1. Run the script for the first time:
   ```
   python csv_xlsx_drive.py --list
   ```
2. You'll be prompted to visit a URL and enter an authentication code
3. This creates a `credentials.json` file for future use

## Security Notes
- Keep `client_secrets.json` and `credentials.json` private
- Add them to `.gitignore` if using version control
- The OAuth credentials allow access to your entire Google Drive

## Usage Examples

### Upload CSV to Google Drive as XLSX:
```bash
python csv_xlsx_drive.py --upload messages.csv --title "KQ1 Hebrew Translation"
```

### Download and convert back to CSV:
```bash
python csv_xlsx_drive.py --download --file-id YOUR_FILE_ID --output messages_updated.csv
```

### List all files:
```bash
python csv_xlsx_drive.py --list
```

### Local conversion only:
```bash
# CSV to XLSX
python csv_xlsx_drive.py --csv-to-xlsx messages.csv messages.xlsx

# XLSX to CSV  
python csv_xlsx_drive.py --xlsx-to-csv messages.xlsx messages.csv
```

## Collaborative Workflow

1. **Upload**: Convert your CSV to XLSX and upload to Google Drive
2. **Share**: The script creates a shareable link with edit permissions
3. **Collaborate**: Friends can open in Google Sheets, add comments, edit translations
4. **Download**: Use the file ID to download updated version back to CSV
5. **Integrate**: Use your existing tools to import the updated CSV

## Excel/Google Sheets Features

The XLSX file will have:
- **Column A**: Room number
- **Column B**: Message index  
- **Column C**: English original (50 char width)
- **Column D**: Hebrew translation (RTL aligned, 50 char width)
- **Column E**: Comments (30 char width)

Your collaborators can:
- Add comments using Google Sheets comment feature
- Edit Hebrew translations directly in cells
- Use Google Sheets real-time collaboration
- View edit history and revert changes
- Filter and sort by room or message type
