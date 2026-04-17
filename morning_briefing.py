import sys
import requests
import json
import time

# 1. Initialize output variables
summaryText = "Initializing..."
csvDeviceStatus = "product_type,online,offline,recovered"
csvEventLog = "network_name,network_id,device_name,serial,mac,product_type,start_ts,end_ts"
csvAssurance = "network_name,network_id,overall_score,category,subcategory,subcategory_score,subcategory_trend,weight_count,weight_percentage"
csvWanUplink = "network_id,serial,uplink,target_ip,timestamp,loss_percent,latency_ms"
csvChannel = "network_id,band,wifi_pct,non_wifi_pct,total_pct"
csvVpnPeer = "device_serial,peer_name,reachability"
csvDeviceUtilization = "network_id,network_name,device_name,device_serial,device_model,used_median_percent"
emptyHistory = "--- Chat History Reset ---"

try:
    api_key = sys.argv[1].strip()
    org_id = sys.argv[2].strip()
    headers = {"X-Cisco-Meraki-API-Key": api_key, "Content-Type": "application/json", "Accept": "application/json"}

    # ==========================================
    # 0. Create Name Resolution Dictionaries
    # ==========================================
    res_nets = requests.get(f"https://api.meraki.com/api/v1/organizations/{org_id}/networks", headers=headers)
    res_nets.raise_for_status()
    net_id_to_name = {n.get("id"): n.get("name", "Unknown") for n in res_nets.json()}

    res_devs = requests.get(f"https://api.meraki.com/api/v1/organizations/{org_id}/devices", headers=headers)
    res_devs.raise_for_status()
    serial_to_netid = {d.get("serial"): d.get("networkId") for d in res_devs.json()}

    def get_net_name_by_serial(serial):
        nid = serial_to_netid.get(serial)
        return net_id_to_name.get(nid, "Unknown Network")

    # ==========================================
    # 1. Device Status & Event Log
    # ==========================================
    res_status = requests.get(f"https://api.meraki.com/api/v1/organizations/{org_id}/assurance/devices/statuses/overview?timespan=3600", headers=headers)
    res_status.raise_for_status()
    data_status = res_status.json()

    csv_status_lines = ["product_type,online,offline,recovered"]
    total_online, total_offline = 0, 0
    for item in data_status.get("byProductType", []):
        pt = item.get("productType", "unknown")
        on, off, rec = item.get("online", 0), item.get("offline", 0), item.get("recovered", 0)
        csv_status_lines.append(f"{pt},{on},{off},{rec}")
        total_online += on; total_offline += off
    csvDeviceStatus = "\n".join(csv_status_lines)

    csv_event_lines = ["network_name,network_id,device_name,serial,mac,product_type,start_ts,end_ts"]
    impacted_devices = data_status.get("byImpactedDevice", [])
    for item in impacted_devices:
        net_name = item.get("network", {}).get("name", "").replace(",", " ")
        net_id = item.get("network", {}).get("id", "")
        dev_name = item.get("device", {}).get("name", "").replace(",", " ")
        serial = item.get("device", {}).get("serial", "")
        mac = item.get("device", {}).get("mac", "")
        pt = item.get("device", {}).get("productType", "")
        intervals = item.get("offlineIntervals", [])
        if not intervals:
            csv_event_lines.append(f"{net_name},{net_id},{dev_name},{serial},{mac},{pt},,")
        else:
            for interval in intervals:
                csv_event_lines.append(f"{net_name},{net_id},{dev_name},{serial},{mac},{pt},{interval.get('startTs','')},{interval.get('endTs','')}")
    csvEventLog = "\n".join(csv_event_lines)

    # ==========================================
    # 2. Assurance Scores
    # ==========================================
    res_score = requests.get(f"https://api.meraki.com/api/v1/organizations/{org_id}/assurance/scores?timespan=7200", headers=headers)
    res_score.raise_for_status()
    data_score = res_score.json()

    csv_assurance_lines = ["network_name,network_id,overall_score,category,subcategory,subcategory_score,subcategory_trend,weight_count,weight_percentage"]
    scored_networks = []
    for item in data_score:
        net_name = item.get("network", {}).get("name", "").replace(",", " ")
        net_id = item.get("network", {}).get("id", "")
        overall_score = item.get("score")
        if overall_score is not None:
            scored_networks.append({"name": net_name, "score": overall_score, "trend": item.get("trend", 0)})
        
        for cat in item.get("byCategory", []):
            cat_name = cat.get("name", "")
            for subcat in cat.get("bySubcategory", []):
                csv_assurance_lines.append(f"{net_name},{net_id},{overall_score if overall_score is not None else ''},{cat_name},{subcat.get('name','')},{subcat.get('score','') if subcat.get('score') is not None else ''},{subcat.get('trend','') if subcat.get('trend') is not None else ''},{subcat.get('weight',{}).get('count','')},{subcat.get('weight',{}).get('percentage','')}")
    csvAssurance = "\n".join(csv_assurance_lines)

    # ==========================================
    # 3. WAN Uplink Loss & Latency (Target: 8.8.8.8)
    # ==========================================
    res_wan = requests.get(f"https://api.meraki.com/api/v1/organizations/{org_id}/devices/uplinksLossAndLatency?timespan=40&ip=8.8.8.8", headers=headers)
    res_wan.raise_for_status()
    data_wan = res_wan.json()

    csv_wan_lines = ["network_id,serial,uplink,target_ip,timestamp,loss_percent,latency_ms"]
    latency_list = []
    loss_list = []
    
    for item in data_wan:
        net_id, serial, uplink, ip = item.get("networkId", ""), item.get("serial", ""), item.get("uplink", ""), item.get("ip", "")
        time_series = item.get("timeSeries", [])
        if not time_series:
            csv_wan_lines.append(f"{net_id},{serial},{uplink},{ip},,,")
        else:
            for ts_data in time_series:
                lat = ts_data.get('latencyMs')
                loss = ts_data.get('lossPercent')
                if lat is not None:
                    latency_list.append({"serial": serial, "net_id": net_id, "latency": lat})
                if loss is not None:
                    loss_list.append({"serial": serial, "net_id": net_id, "loss": loss})
                csv_wan_lines.append(f"{net_id},{serial},{uplink},{ip},{ts_data.get('ts','')},{loss if loss is not None else ''},{lat if lat is not None else ''}")
    csvWanUplink = "\n".join(csv_wan_lines)

    # ==========================================
    # 4. Channel Utilization (byNetwork)
    # ==========================================
    res_channel = requests.get(f"https://api.meraki.com/api/v1/organizations/{org_id}/wireless/devices/channelUtilization/byNetwork?timespan=7200", headers=headers)
    res_channel.raise_for_status()
    data_channel = res_channel.json()

    csv_channel_lines = ["network_id,band,wifi_pct,non_wifi_pct,total_pct"]
    channel_list = []
    for item in data_channel:
        net_id = item.get("network", {}).get("id", "")
        net_name = net_id_to_name.get(net_id, "Unknown Network")
        for band_data in item.get("byBand", []):
            band = band_data.get("band", "")
            wifi = band_data.get("wifi", {}).get("percentage", "")
            non_wifi = band_data.get("nonWifi", {}).get("percentage", "")
            total = band_data.get("total", {}).get("percentage", "")
            csv_channel_lines.append(f"{net_id},{band},{wifi},{non_wifi},{total}")
            
            if total != "":
                channel_list.append({"net_name": net_name, "band": band, "total": float(total)})
    csvChannel = "\n".join(csv_channel_lines)

    # ==========================================
    # 5. VPN Peer Status
    # ==========================================
    res_vpn = requests.get(f"https://api.meraki.com/api/v1/organizations/{org_id}/appliance/vpn/statuses", headers=headers)
    res_vpn.raise_for_status()
    data_vpn = res_vpn.json()

    csv_vpn_lines = ["device_serial,peer_name,reachability"]
    unreachable_peers = []
    for item in data_vpn:
        serial = item.get("deviceSerial", "")
        for peer in item.get("merakiVpnPeers", []):
            reach = peer.get("reachability", "")
            name = peer.get("networkName", "").replace(",", " ")
            csv_vpn_lines.append(f"{serial},{name},{reach}")
            if reach != "reachable": unreachable_peers.append({"serial": serial, "peer": name})
        for peer in item.get("thirdPartyVpnPeers", []):
            reach = peer.get("reachability", "")
            name = peer.get("name", "").replace(",", " ")
            csv_vpn_lines.append(f"{serial},{name},{reach}")
            if reach != "reachable": unreachable_peers.append({"serial": serial, "peer": name})
    csvVpnPeer = "\n".join(csv_vpn_lines)

    # ==========================================
    # 6. Device Utilization (Memory) - Async Handling
    # ==========================================
    url_mem = f"https://api.meraki.com/api/v1/organizations/{org_id}/devices/system/memory/usage/history/byInterval?timespan=3600"
    res_mem = requests.get(url_mem, headers=headers)
    res_mem.raise_for_status()
    data_mem = res_mem.json()

    if isinstance(data_mem, str):
        async_url = data_mem.strip()
        print(f"Memory API returned an async URL. Polling: {async_url}")
        for _ in range(5):
            time.sleep(5)
            res_mem = requests.get(async_url, headers=headers)
            if res_mem.status_code == 200:
                data_mem = res_mem.json()
                if not isinstance(data_mem, str):
                    break
        if isinstance(data_mem, str):
            raise ValueError(f"Memory API Error: Async polling timed out. URL: {async_url}")

    mem_items = []
    if isinstance(data_mem, dict):
        mem_items = data_mem.get("items", [])
    elif isinstance(data_mem, list):
        mem_items = data_mem
    else:
        raise ValueError(f"Memory API Error: Unexpected data format. Type: {type(data_mem)}")

    csv_mem_lines = ["network_id,network_name,device_name,device_serial,device_model,used_median_percent"]
    mem_list = []
    
    for item in mem_items:
        if not isinstance(item, dict):
            continue
            
        net_id = item.get("network", {}).get("id", "")
        net_name = item.get("network", {}).get("name", "").replace(",", " ")
        dev_name = (item.get("name") or "").replace(",", " ")
        serial = item.get("serial", "")
        model = item.get("model", "")
        
        intervals = item.get("intervals", [])
        used_pct = ""
        
        if intervals and isinstance(intervals, list) and isinstance(intervals[0], dict):
            latest_interval = intervals[0]
            memory_data = latest_interval.get("memory", {})
            used = memory_data.get("used", {}).get("median")
            free = memory_data.get("free", {}).get("median")
            
            if used is not None and free is not None:
                total = used + free
                if total > 0:
                    used_pct = round((used / total) * 100, 1)
                    mem_list.append({"name": dev_name or serial, "pct": used_pct})
                    
        csv_mem_lines.append(f"{net_id},{net_name},{dev_name},{serial},{model},{used_pct}")

    csvDeviceUtilization = "\n".join(csv_mem_lines)

    # ==========================================
    # Webex Summary Text Generation
    # ==========================================
    summaryText = "## 📊 Morning Briefing: Network Health Report\n\n"

    # 1. Device Status
    summaryText += f"**1️⃣ Device Status**\n"
    summaryText += f"- 🟢 **Online:** {total_online} devices\n"
    summaryText += f"- 🔴 **Offline:** {total_offline} devices\n"
    if impacted_devices:
        summaryText += "- ⚠️ **Top 5 Devices with Offline History (Last 1hr):**\n"
        for i, item in enumerate(impacted_devices[:5], 1):
            net_name = item.get("network", {}).get("name", "Unknown").replace(",", " ")
            dev_name = item.get("device", {}).get("name", "Unknown").replace(",", " ")
            pt = item.get("device", {}).get("productType", "unknown")
            summaryText += f"  {i}. `[{pt}]` {dev_name} (Network: *{net_name}*)\n"
    else:
        summaryText += "- 🟢 **No offline history detected in the last hour.**\n"
    summaryText += "\n---\n\n"

    # 2. Assurance Score
    summaryText += f"**2️⃣ Assurance Score (Network Health)**\n"
    scored_networks.sort(key=lambda x: x["score"])
    if scored_networks:
        summaryText += f"- 📊 **Networks Evaluated:** {len(scored_networks)}\n"
        summaryText += "- ⚠️ **Top 5 Networks with Lowest Scores:**\n"
        for i, item in enumerate(scored_networks[:5], 1):
            trend = item.get('trend')
            if trend is None: trend = 0
            trend_str = f"(↓{abs(trend)})" if trend < 0 else f"(↑{trend})" if trend > 0 else "(±0)"
            summaryText += f"  {i}. **{item['name']}** : Score **{item['score']}** {trend_str}\n"
    else:
        summaryText += "- ℹ️ No Assurance Score data available at this time.\n"
    summaryText += "\n---\n\n"

    # 3. WAN Uplink
    summaryText += f"**3️⃣ WAN Uplink (Loss & Latency)**\n"
    latency_list_filtered = [x for x in latency_list if x["latency"] > 0.0]
    latency_list_filtered.sort(key=lambda x: x["latency"], reverse=True)
    if latency_list_filtered:
        summaryText += "- ⚠️ **Top 3 Devices with High Latency:**\n"
        seen_serials = set()
        count = 1
        for item in latency_list_filtered:
            if item["serial"] not in seen_serials:
                net_name = net_id_to_name.get(item["net_id"], "Unknown Network")
                summaryText += f"  {count}. {net_name} - Serial: `{item['serial']}` (Latency: **{item['latency']} ms**)\n"
                seen_serials.add(item["serial"])
                count += 1
            if count > 3: break
    else:
        summaryText += "- 🟢 No high latency detected.\n"

    loss_list_filtered = []
    for x in loss_list:
        if x["loss"] > 0:
            is_valid = True
            if x["loss"] == 100.0:
                for l_item in latency_list:
                    if l_item["serial"] == x["serial"] and l_item["latency"] == 0.0:
                        is_valid = False
                        break
            if is_valid:
                loss_list_filtered.append(x)

    loss_list_filtered.sort(key=lambda x: x["loss"], reverse=True)
    if loss_list_filtered:
        summaryText += "- ⚠️ **Top 3 Devices with Packet Loss:**\n"
        seen_serials = set()
        count = 1
        for item in loss_list_filtered:
            if item["serial"] not in seen_serials:
                net_name = net_id_to_name.get(item["net_id"], "Unknown Network")
                summaryText += f"  {count}. {net_name} - Serial: `{item['serial']}` (Loss: **{item['loss']} %**)\n"
                seen_serials.add(item["serial"])
                count += 1
            if count > 3: break
    else:
        summaryText += "- 🟢 No packet loss detected.\n"
    summaryText += "\n---\n\n"

    # 4. VPN Peer Status
    summaryText += f"**4️⃣ VPN Peer Status**\n"
    if unreachable_peers:
        summaryText += f"- 🔴 **Disconnected VPN Tunnels:** {len(unreachable_peers)}\n"
        for i, peer in enumerate(unreachable_peers[:5], 1):
            src_net = get_net_name_by_serial(peer["serial"])
            summaryText += f"  {i}. Connection from [*{src_net}*] to [*{peer['peer']}*] is DOWN\n"
    else:
        summaryText += "- 🟢 All VPN peers are Reachable.\n"
    summaryText += "\n---\n\n"

    # 5. Device Utilization
    summaryText += f"**5️⃣ Device Resource (Memory Utilization)**\n"
    mem_data_parsed = []
    for line in csvDeviceUtilization.split("\n")[1:]:
        parts = line.split(",")
        if len(parts) >= 6 and parts[5]:
            try:
                mem_data_parsed.append({
                    "net_name": parts[1],
                    "dev_name": parts[2] if parts[2] else parts[3],
                    "pct": float(parts[5])
                })
            except ValueError:
                continue
                
    mem_data_parsed.sort(key=lambda x: x["pct"], reverse=True)
    if mem_data_parsed:
        summaryText += "- ⚠️ **Top 3 Devices with High Memory Usage:**\n"
        for i, item in enumerate(mem_data_parsed[:3], 1):
            summaryText += f"  {i}. [*{item['net_name']}*] {item['dev_name']} (**{item['pct']}%**)\n"
    else:
        summaryText += "- 🟢 No memory utilization data available.\n"
    summaryText += "\n---\n\n"

    # 6. Channel Utilization
    summaryText += f"**6️⃣ Channel Utilization (Wireless Congestion)**\n"
    if channel_list:
        band_data = {"2.4": [], "5": [], "6": []}
        for item in channel_list:
            band = str(item["band"])
            if band in band_data:
                band_data[band].append(item)
        
        for band in ["2.4", "5", "6"]:
            band_data[band].sort(key=lambda x: x["total"], reverse=True)
            if band_data[band]:
                summaryText += f"- 📡 **Top 3 Networks on {band}GHz Band:**\n"
                for i, item in enumerate(band_data[band][:3], 1):
                    summaryText += f"  {i}. {item['net_name']} : Utilization **{item['total']}%**\n"
    else:
        summaryText += "- ℹ️ No channel utilization data available.\n"

    summaryText += "\n\n> 💡 *If you need detailed root cause analysis or troubleshooting steps, please mention this Bot and ask a question.*"
    print("All APIs fetched and CSVs generated successfully.")

except Exception as e:
    error_msg = f"❌ **Error occurred in data collection script**\n\nDetails: `{str(e)}`"
    print(error_msg)
    summaryText = error_msg
