# Meraki Autonomous AI ChatOps

Empowering IT Admins with Webex-Integrated Autonomous ChatOps via Cisco Meraki Workflows and Gemini API.

This project transforms Meraki Workflows into a highly intelligent, context-aware Network Assistant. It proactively generates a daily network health report and reactively answers complex troubleshooting questions using GenAI (Gemini 2.5 Flash).

## ⚠️ IMPORTANT: Data Privacy & Security Warning (Please Read First)

This solution transmits sensitive network telemetry data (including Device Names, MAC Addresses, Serial Numbers, and Internal IP Addresses) to an external Large Language Model (Google Gemini API) for analysis. 

**When using the Google Gemini API (via Google AI Studio):**
- **Free Tier (Not Recommended for Production):** If you use the free tier API key, Google's Terms of Service state that your input data **may be used to train and improve their models**, and may be reviewed by human reviewers. **DO NOT** use the free tier if your network data contains highly confidential or proprietary information.
- **Pay-as-you-go / Paid Tier (Recommended):** If you set up a billing account (Pay-as-you-go), Google explicitly states that your data **will NOT be used for training** their models, ensuring enterprise-grade data privacy. 

**Best Practice:** We strongly advise enabling a billing account on Google AI Studio and setting a strict budget alert (e.g., $1/month) to ensure your data remains private while keeping costs negligible. Use this tool at your own risk and ensure compliance with your organization's security policies.

---

## 🛑 Note on Dashboard API Access Restrictions (IP Whitelisting)

If your Meraki Organization enforces strict **Dashboard API Access Restrictions (IP Whitelisting)**, this solution may fail to execute API calls.

Although Meraki Workflows is hosted within the Meraki Dashboard environment, the Python scripts executed by Workflows make API calls originating from external cloud IP addresses. If these dynamic IP addresses are not whitelisted, the Meraki API will block the requests (resulting in 403 Forbidden or timeout errors).

**Workaround:** Currently, maintaining a whitelist for the dynamic IP ranges used by the Workflows infrastructure is highly impractical for enterprise security. If you encounter this issue, please contact **Meraki Support** to inquire about the specific IP ranges that need to be allowed, or temporarily disable the IP restriction for testing purposes. We hope for a seamless backend integration in future Meraki updates.

---

## Features
- **100% Serverless**: Runs entirely on Cisco Meraki Workflows. No external databases or servers required.
- **Proactive Morning Briefing**: Automated daily health reports delivered to Webex.
- **Reactive ChatOps**: Interactive troubleshooting via Webex mentions.
- **Cost-Optimized & Accurate**: Transforms complex JSON payloads into Tidy Data (CSV) to minimize LLM token consumption and prevent AI hallucinations.

<img width="1444" height="744" alt="Image" src="https://github.com/user-attachments/assets/f305a156-35f7-428e-af9a-144be0a46b83" />

## Prerequisites
- A Cisco Meraki Organization with Workflows enabled.
- A Webex Bot Access Token and Room ID.
- A Google Gemini API Key (Gemini 2.5 Flash) - **Paid tier recommended for privacy**.

## Setup Guide

### Step 1: Configure Global Variables in Workflows
Navigate to **Automation -> Variables** in the Meraki Dashboard and create the following **Global Variables** (Data Type: `String`):

1. `Gemini_API_Key` (Value: Your Gemini API Key)
2. `Webex_Bot_Token` (Value: Your Webex Bot Token)
3. `Webex_Room_ID` (Value: Your Webex Room ID)
4. `CSV_DeviceStatus` (Value: Leave blank)
5. `CSV_EventLog` (Value: Leave blank)
6. `CSV_Assurance` (Value: Leave blank)
7. `CSV_WAN_Uplink` (Value: Leave blank)
8. `CSV_Channel` (Value: Leave blank)
9. `CSV_VPN_Peer` (Value: Leave blank)
10. `CSV_DeviceUtilization` (Value: Leave blank)
11. `Chat_History` (Value: `--- Chat History Reset ---`)

### Step 2: Create the "Morning Briefing" Workflow
1. Go to **Automation -> Workspace** and create a new Blank Custom Workflow.
2. Name it `Morning Briefing (MVP)`.
3. Add an **Execute Python Script** activity.
4. Add 2 Script Arguments:
   - `Global -> Gemini_API_Key`
   - `Global -> Organization_ID` (Create this global variable if you haven't already)
5. Paste the code from `morning_briefing.py` into the script editor.
6. Add 8 **Script Queries** (`summaryText`, `csvDeviceStatus`, `csvEventLog`, `csvAssurance`, `csvWanUplink`, `csvChannel`, `csvVpnPeer`, `csvDeviceUtilization`, `emptyHistory`).
7. Add a **Set Variables** activity to map the 7 CSVs and `emptyHistory` to their corresponding Global Variables.
8. Add another **Execute Python Script** activity to send `summaryText` to Webex.

### Step 3: Create the "ChatOps Responder" Workflow
1. Create a new Blank Custom Workflow named `ChatOps Responder (Gemini)`.
2. Add an Input Variable named `Webhook_Payload` (Data Type: String, String Type: JSON).
3. Add an **Execute Python Script** activity.
4. Map the 11 Script Arguments exactly as defined in the `chatops_responder.py` code.
5. Paste the code from `chatops_responder.py`.
6. Add a **Script Query** named `updatedHistory`.
7. Add a **Set Variables** activity to map `updatedHistory` back to the Global Variable `Chat_History`.

### Step 4: Configure Webhook and Automation Rules
1. Go to **Automation -> Rules -> Webhooks** and create a new Webhook.
2. **CRITICAL**: Set the Request Content Type to `application/json; charset=utf-8`.
3. Register this Webhook URL to your Webex Bot via the Webex Developer API.
4. Go to the **Automation Rules** tab and create two rules:
   - **Schedule Rule**: Trigger `Morning Briefing (MVP)` daily at 8:00 AM.
   - **Webhook Rule**: Trigger `ChatOps Responder (Gemini)` using the Webhook you created, mapping the Request Body to the `Webhook_Payload` input variable.

## Usage
- Check your Webex room every morning for the Network Health Report.
- Mention the bot in Webex (e.g., `@BotName Why is the Assurance Score for "0_White" so low?`) to start troubleshooting.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
