#!/bin/bash

# ============================================
# CPM King Rank Tool - Termux Edition
# ============================================

# --- KONFIGURACIJA ---
FIREBASE_API_KEY="AIzaSyBW1ZbMiUeDZHYUO2bY8Bfnf5rRgrQGPTM"
FIREBASE_LOGIN_URL="https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key=${FIREBASE_API_KEY}"

# Endpointi
URL1="https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating1"
URL2="https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating2"
URL5="https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating5"
URL6="https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating6"

# Telegram (ostavi prazno ako ne želiš logove)
BOT_TOKEN="8691576277:AAG97ec5y9SmEPfWunG_GXwzbdRlPVWQd-s"
CHAT_ID="7183809303"

# Boje
G='\033[92m'
Y='\033[93m'
C='\033[96m'
W='\033[97m'
R='\033[91m'
RE='\033[0m'

# ============================================
# POMOĆNE FUNKCIJE
# ============================================

send_telegram() {
    local msg="$1"
    if [ -n "8663420665:AAENhWlvRPuv_bjHEVE3tqseeWqgGOJLFB0 " ] && [ -n " 8884756222 " ]; then
        curl -s -X POST "https://api.telegram.org/bot${8663420665:AAENhWlvRPuv_bjHEVE3tqseeWqgGOJLFB0 }/sendMessage" \
            -H "Content-Type: application/json" \
            -d "{\"chat_id\":${CHAT_ID},\"text\":\"${msg}\"}" > /dev/null 2>&1
    fi
}

generate_payload() {
    python3 -c "
import json
rating_data = {
    'cars': 100000, 'car_fix': 100000, 'car_collided': 100000,
    'car_exchange': 100000, 'car_trade': 100000, 'car_wash': 100000,
    'slicer_cut': 100000, 'drift_max': 100000, 'drift': 100000,
    'cargo': 100000, 'delivery': 100000, 'taxi': 100000,
    'levels': 100000, 'gifts': 100000, 'fuel': 100000,
    'offroad': 100000, 'speed_banner': 100000, 'reactions': 100000,
    'police': 100000, 'run': 100000, 'real_estate': 100000,
    't_distance': 100000, 'treasure': 100000, 'block_post': 100000,
    'push_ups': 100000, 'burnt_tire': 100000, 'passanger_distance': 100000,
    'time': 1000000000, 'race_win': 3000
}
payload = {'data': json.dumps({'RatingData': rating_data})}
print(json.dumps(payload))
"
}

login_firebase() {
    local email="$1"
    local password="$2"
    
    local payload
    payload=$(python3 -c "
import json
print(json.dumps({
    'clientType': 'CLIENT_TYPE_ANDROID',
    'email': '${email}',
    'password': '${password}',
    'returnSecureToken': True
}))
")
    
    local response
    response=$(curl -s -X POST "$FIREBASE_LOGIN_URL" \
        -H "User-Agent: Dalvik/2.1.0 (Linux; U; Android 12)" \
        -H "Content-Type: application/json" \
        -d "$payload")
    
    local token
    token=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('idToken',''))")
    
    if [ -n "$token" ]; then
        echo "$token"
    else
        echo ""
    fi
}

set_rank() {
    local token="$1"
    local url="$2"
    local name="$3"
    
    local payload
    payload=$(generate_payload)
    
    local response http_code body
    response=$(curl -s -w "\n%{http_code}" -X POST "$url" \
        -H "Authorization: Bearer ${token}" \
        -H "Content-Type: application/json" \
        -H "User-Agent: okhttp/3.12.13" \
        -d "$payload")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "200" ]; then
        echo -e "${G}[+] ${name} → OK${RE}"
        return 0
    else
        echo -e "${R}[-] ${name} → FAILED (${http_code})${RE}"
        echo -e "${R}    ${body}${RE}"
        return 1
    fi
}

send_all() {
    local token="$1"
    echo -e "${Y}[*] Šaljem na sve endpointe...${RE}"
    set_rank "$token" "$URL1" "SetUserRating1"
    set_rank "$token" "$URL2" "SetUserRating2"
    set_rank "$token" "$URL5" "SetUserRating5"
    set_rank "$token" "$URL6" "SetUserRating6"
}

banner() {
    clear
    echo -e "${G}##############################################"
    echo -e "#                                            #"
    echo -e "#        ${W}CAR PARKING MULTIPLAYER             ${G}#"
    echo -e "#           ${Y}KING RANK SERVICE                ${G}#"
    echo -e "#                                            #"
    echo -e "#        ${C}IG: @anonymo.cpm                    ${G}#"
    echo -e "#        ${C}Owner: @anonymo.cpm                 ${G}#"
    echo -e "#                                            #"
    echo -e "##############################################${RE}"
    echo -e ""
    echo -e "${W}----------------------------------------------${RE}"
    echo -e "1. King Rank (All Endpoints)"
    echo -e "2. SetUserRating1 Only"
    echo -e "3. SetUserRating2 Only"
    echo -e "4. SetUserRating5 Only"
    echo -e "5. SetUserRating6 Only"
    echo -e "6. Exit"
    echo -e "${W}----------------------------------------------${RE}"
}

# ============================================
# GLAVNI PROGRAM
# ============================================

while true; do
    banner
    read -p "$(echo -e ${W}Select an option: ${RE})" choice
    
    if [ "$choice" = "1" ] || [ "$choice" = "2" ] || [ "$choice" = "3" ] || [ "$choice" = "4" ] || [ "$choice" = "5" ]; then
        read -p "$(echo -e ${W}Enter Email: ${RE})" email
        read -p "$(echo -e ${W}Enter Password: ${RE})" password
        
        echo -e "\n${Y}[*] Connecting to Firebase...${RE}"
        auth_token=$(login_firebase "$email" "$password")
        
        if [ -n "$auth_token" ]; then
            echo -e "${G}[+] Login successful!${RE}"
            sleep 1
            
            case "$choice" in
                1)
                    send_all "$auth_token"
                    send_telegram "✅ King Rank applied to ${email} (All Endpoints)"
                    echo -e "\n${G}[+] Done! King Rank is now active.${RE}"
                    ;;
                2)
                    set_rank "$auth_token" "$URL1" "SetUserRating1"
                    send_telegram "✅ SetUserRating1 applied to ${email}"
                    ;;
                3)
                    set_rank "$auth_token" "$URL2" "SetUserRating2"
                    send_telegram "✅ SetUserRating2 applied to ${email}"
                    ;;
                4)
                    set_rank "$auth_token" "$URL5" "SetUserRating5"
                    send_telegram "✅ SetUserRating5 applied to ${email}"
                    ;;
                5)
                    set_rank "$auth_token" "$URL6" "SetUserRating6"
                    send_telegram "✅ SetUserRating6 applied to ${email}"
                    ;;
            esac
            echo -e "\n${C}Press Enter to continue...${RE}"
            read
        else
            echo -e "\n${R}[-] Login failed! Check credentials.${RE}"
            sleep 2
        fi
        
    elif [ "$choice" = "6" ]; then
        echo -e "${Y}Exiting...${RE}"
        exit 0
    else
        echo -e "${R}Invalid option!${RE}"
        sleep 1
    fi
done
