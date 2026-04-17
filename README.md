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

## 🌟 How It Works (Examples)

### 1. Proactive "Morning Briefing" Report
Every morning at 8:00 AM, the bot posts a beautifully formatted, comprehensive health summary to your Webex room.

> **## 📊 Morning Briefing: Network Health Report**
> 
> **1️⃣ Device Status**
> - 🟢 **Online:** 142 devices
> - 🔴 **Offline:** 3 devices
> - ⚠️ **Top 5 Devices with Offline History (Last 1hr):**
>   1. `[switch]` Core-SW-01 (Network: *Branch-NY*)
>   2. `[wireless]` AP-Lobby (Network: *Retail-London*)
>   3. `[wireless]` AP-Warehouse-02 (Network: *Warehouse-TX*)
>
> **2️⃣ Assurance Score (Network Health)**
> - 📊 **Networks Evaluated:** 45
> - ⚠️ **Top 5 Networks with Lowest Scores:**
>   1. **Branch-NY** : Score **72** (↓15)
>   2. **Retail-London** : Score **82** (↓8)
>   3. **Remote-Worker-01** : Score **92** (±0)
>   4. **Warehouse-TX** : Score **94** (↓6)
>   5. **Branch-Tokyo** : Score **95** (±0)
>
> **3️⃣ WAN Uplink (Loss & Latency)**
> - ⚠️ **Top 3 Devices with High Latency:**
>   1. Retail-London - Serial: `Q2XX-XXXX-XXXX` (Latency: **278.6 ms**)
>   2. Branch-NY - Serial: `Q2YY-YYYY-YYYY` (Latency: **150.2 ms**)
>   3. HQ-Core - Serial: `Q2ZZ-ZZZZ-ZZZZ` (Latency: **45.1 ms**)
> - ⚠️ **Top 3 Devices with Packet Loss:**
>   1. Branch-NY - Serial: `Q2YY-YYYY-YYYY` (Loss: **100.0 %**)
>   2. Remote-Worker-01 - Serial: `Q3AA-AAAA-AAAA` (Loss: **15.5 %**)
>
> **4️⃣ VPN Peer Status**
> - 🔴 **Disconnected VPN Tunnels:** 2
>   1. Connection from [*Branch-NY*] to [*HQ-Core*] is DOWN
>   2. Connection from [*HQ-Core*] to [*Branch-NY*] is DOWN
>
> **5️⃣ Device Resource (Memory Utilization)**
> - ⚠️ **Top 3 Devices with High Memory Usage:**
>   1. [*HQ-Core*] Cam-Entrance-MV21 (**88.1%**)
>   2. [*Branch-Tokyo*] SW-Floor1-MS220 (**50.4%**)
>   3. [*Retail-London*] FW-Main-MX67 (**25.6%**)
>
> **6️⃣ Channel Utilization (Wireless Congestion)**
> - 📡 **Top 3 Networks on 2.4GHz Band:**
>   1. Warehouse-TX : Utilization **41.53%**
>   2. Retail-London : Utilization **16.84%**
>   3. HQ-Core : Utilization **12.15%**
>
> ---
> > 💡 *If you need detailed root cause analysis or troubleshooting steps, please mention this Bot and ask a question.*

### 2. Reactive "ChatOps" Troubleshooting
When you see an issue in the report, simply mention the bot to dive deeper. The AI cross-references all 7 CSV datasets to find the root cause.

**User:**
> `@MerakiBot` Why is the Assurance Score for "Branch-NY" so low?

**MerakiBot (Gemini 2.5 Flash):**
> ### Executive Summary
> The Assurance Score for **Branch-NY** has dropped to 72 primarily due to severe WAN connectivity issues, resulting in a complete VPN tunnel failure and offline devices.
> 
> ### Detailed Analysis
> - **WAN Failure:** The primary appliance in Branch-NY is experiencing **100% packet loss** and high latency (150.2 ms).
> - **VPN Disconnection:** As a direct result of the WAN failure, the Site-to-Site VPN tunnel between **Branch-NY** and **HQ-Core** is currently DOWN.
> - **Device Impact:** The switch `Core-SW-01` in this network was reported offline within the last hour, likely due to the loss of cloud connectivity.
> 
> ### Recommended Actions
> 1. **Check ISP Status:** Contact the local ISP for Branch-NY immediately to verify if there is an ongoing outage.
> 2. **Verify Physical Connections:** Ask a local contact to ensure the WAN cable is securely plugged into the MX appliance.
> 3. **Cellular Failover:** Check if the cellular backup (if configured) has successfully taken over the traffic.

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

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
