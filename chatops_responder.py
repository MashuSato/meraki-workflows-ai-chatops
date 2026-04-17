import sys
import json
import requests

# 1. Receive arguments (11 arguments)
gemini_api_key = sys.argv[1].strip()
webex_token = sys.argv[2].strip()
webhook_payload = sys.argv[3]
csv_status = sys.argv[4]
csv_event = sys.argv[5]
csv_assurance = sys.argv[6]
csv_wan_uplink = sys.argv[7]
csv_channel = sys.argv[8]
csv_vpn_peer = sys.argv[9]
csv_device_utilization = sys.argv[10]
chat_history = sys.argv[11]

ai_response_text = "Processing..."

try:
    payload_data = json.loads(webhook_payload)
    message_id = payload_data.get("data", {}).get("id")
    room_id = payload_data.get("data", {}).get("roomId")

    if not message_id or not room_id:
        raise ValueError("Could not retrieve message ID or room ID from Webhook payload.")

    # Fetch the actual question text from Webex API
    msg_url = f"https://webexapis.com/v1/messages/{message_id}"
    headers = {"Authorization": f"Bearer {webex_token}"}
    msg_res = requests.get(msg_url, headers=headers)
    msg_res.raise_for_status()
    
    user_question = msg_res.json().get("text", "").strip()
    if " " in user_question:
        user_question = user_question.split(" ", 1)[1]

    # 4. Create Prompt for Gemini
    prompt = f"""
You are a highly skilled Senior Cisco Meraki Network Engineer.
Analyze the following 7 network datasets (CSV format) and the "Recent Chat History" to answer the user's question.

【CRITICAL RULES FOR YOUR RESPONSE】
1. **DO NOT expose raw data structures**: Never mention internal variable names like `network_id`, `serial`, `target_ip`, `loss_percent`, or `latency_ms` in your response. 
2. **Be intuitive and professional**: Explain the situation in plain English as if you are reporting to an IT Director. Use actual network names and device names instead of IDs or serials whenever possible.
3. **Structure your answer**: Always use Markdown. Start with a brief "Executive Summary", followed by "Detailed Analysis", and end with "Recommended Actions".
4. **Cross-reference data**: The CSVs are linked by `network_id` and `serial`. If a network has a low Assurance Score, cross-check the WAN Uplink, VPN Peer, or Device Utilization CSVs to find the root cause.

【CSV Data Definitions】
1. <device_status_summary>
- Overview: Count of online/offline devices by product type.
{csv_status}
</device_status_summary>

2. <offline_event_log>
- Overview: Details of currently offline devices and their downtime.
{csv_event}
</offline_event_log>

3. <assurance_score_data>
- Overview: Network health scores. A low `overall_score` indicates an issue. Check the `subcategory` and `subcategory_score` to identify the root cause.
{csv_assurance}
</assurance_score_data>

4. <wan_uplink_data>
- Overview: WAN link quality (packet loss and latency) for MX/Z3 appliances. High latency or loss indicates ISP issues or congestion.
{csv_wan_uplink}
</wan_uplink_data>

5. <channel_utilization_data>
- Overview: Wireless channel utilization by network. High `non_wifi_pct` means non-Wi-Fi interference (e.g., microwaves). High `wifi_pct` means AP congestion.
{csv_channel}
</channel_utilization_data>

6. <vpn_peer_data>
- Overview: Site-to-Site VPN peer status. `unreachable` means the tunnel is down.
{csv_vpn_peer}
</vpn_peer_data>

7. <device_utilization_data>
- Overview: Device memory utilization. High `used_median_percent` (e.g., >80%) can cause device freezes or reboots.
{csv_device_utilization}
</device_utilization_data>

<chat_history>
{chat_history}
</chat_history>

【User's Question】
{user_question}
"""

    # 5. Call Gemini API (2.5 Flash)
    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_api_key}"
    gemini_headers = {"Content-Type": "application/json"}
    gemini_payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    gemini_res = requests.post(gemini_url, headers=gemini_headers, json=gemini_payload)
    gemini_res.raise_for_status()
    
    ai_response_text = gemini_res.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "AI response was empty.")
    print("Gemini analysis completed successfully.")

except Exception as e:
    ai_response_text = f"❌ **Error occurred during AI analysis**\n\nDetails:\n```\n{str(e)}\n```"
    room_id = room_id if 'room_id' in locals() else None
    print(ai_response_text)

# 6. Update Chat History
new_history = chat_history + f"\nUser: {user_question}\nAI: {ai_response_text}\n"
if len(new_history) > 4000:
    new_history = "..." + new_history[-4000:]

# 7. Reply to Webex
if room_id:
    reply_url = "https://webexapis.com/v1/messages"
    reply_headers = {
        "Authorization": f"Bearer {webex_token}",
        "Content-Type": "application/json"
    }
    reply_payload = {
        "roomId": room_id,
        "markdown": ai_response_text
    }
    try:
        requests.post(reply_url, headers=reply_headers, json=reply_payload)
        print("Successfully replied to Webex.")
    except Exception as e:
        print(f"Failed to send reply to Webex: {e}")

# 8. Pass history to Script Queries
updatedHistory = new_history
