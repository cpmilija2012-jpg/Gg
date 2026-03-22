#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (C) Anonymo - Sva prava zadržana
Autor: Anonymo
Datum: 22. Mart, 2026.
"""

import requests
import json
import random
import os
import signal
import sys
from time import sleep
from rich.console import Console
from rich.prompt import Prompt, IntPrompt

# --- KONFIGURACIJA ---
BASE_URL: str = "https://cpmnuker.anasov.ly"
__CHANNEL_USERNAME__ = "AnonymoChannel"
__GROUP_USERNAME__   = "AnonymoChat"

# ==========================================================
# KOMPLETNA KLASA: AnonymoControl
# ==========================================================

class AnonymoControl:
    def __init__(self, access_key) -> None:
        self.auth_token = None
        self.access_key = access_key
        
    def prijavi_se(self, email, password) -> int:
        payload = { "account_email": email, "account_password": password }
        params = { "key": self.access_key }
        response = requests.post(f"{BASE_URL}/api/account_login", params=params, data=payload)
        res = json.loads(response.text)
        if res.get("ok"): self.auth_token = res.get("auth")
        return res.get("error")
    
    def registruj_se(self, email, password) -> int:
        payload = { "account_email": email, "account_password": password }
        params = { "key": self.access_key }
        response = requests.post(f"{BASE_URL}/api/account_register", params=params, data=payload)
        res = json.loads(response.text)
        if res.get("ok"): self.auth_token = res.get("auth")
        return res.get("error")
    
    def obrisi_nalog(self) -> None:
        payload = { "account_auth": self.auth_token }
        params = { "key": self.access_key }
        requests.post(f"{BASE_URL}/api/account_delete", params=params, data=payload)

    def preuzmi_podatke(self) -> any:
        payload = { "account_auth": self.auth_token }
        params = { "key": self.access_key }
        return json.loads(requests.post(f"{BASE_URL}/api/get_data", params=params, data=payload).text)
    
    def postavi_rang(self) -> bool:
        payload = { "account_auth": self.auth_token }
        params = { "key": self.access_key }
        return json.loads(requests.post(f"{BASE_URL}/api/set_rank", params=params, data=payload).text).get("ok")
    
    def preuzmi_kljuc_podatke(self) -> any:
        params = { "key": self.access_key }
        return json.loads(requests.get(f"{BASE_URL}/api/get_key_data", params=params).text)
    
    def postavi_money(self, amount) -> bool:
        payload = { "account_auth": self.auth_token, "amount": amount }
        params = { "key": self.access_key }
        return json.loads(requests.post(f"{BASE_URL}/api/set_money", params=params, data=payload).text).get("ok")
    
    def postavi_coins(self, amount) -> bool:
        payload = { "account_auth": self.auth_token, "amount": amount }
        params = { "key": self.access_key }
        return json.loads(requests.post(f"{BASE_URL}/api/set_coins", params=params, data=payload).text).get("ok")
    
    def postavi_ime(self, name) -> bool:
        payload = { "account_auth": self.auth_token, "name": name }
        params = { "key": self.access_key }
        return json.loads(requests.post(f"{BASE_URL}/api/set_name", params=params, data=payload).text).get("ok")
    
    def postavi_localid(self, id) -> bool:
        payload = { "account_auth": self.auth_token, "id": id }
        params = { "key": self.access_key }
        return json.loads(requests.post(f"{BASE_URL}/api/set_id", params=params, data=payload).text).get("ok")

    def postavi_tablice(self) -> bool:
        payload = { "account_auth": self.auth_token }
        params = { "key": self.access_key }
        return json.loads(requests.post(f"{BASE_URL}/api/set_plates", params=params, data=payload).text).get("ok")
    
    def obrisi_prijatelje(self) -> bool:
        payload = { "account_auth": self.auth_token }
        params = { "key": self.access_key }
        return json.loads(requests.post(f"{BASE_URL}/api/delete_friends", params=params, data=payload).text).get("ok")
    
    def otkljucaj_w16(self) -> bool:
        payload = { "account_auth": self.auth_token }
        params = { "key": self.access_key }
        return json.loads(requests.post(f"{BASE_URL}/api/unlock_w16", params=params, data=payload).text).get("ok")
    
    def otkljucaj_sirene(self) -> bool:
        payload = { "account_auth": self.auth_token }
        params = { "key": self.access_key }
        return json.loads(requests.post(f"{BASE_URL}/api/unlock_horns", params=params, data=payload).text).get("ok")

# ==========================================================
# POMOĆNE FUNKCIJE
# ==========================================================

def signal_handler(sig, frame):
    print("\n Bye Bye...")
    sys.exit(0)

def banner(console):
    os.system('cls' if os.name == 'nt' else 'clear')
    console.print("[bold green]♕ AnonymoControl[/bold green]: Car Parking Multiplayer Tool.")
    console.print(f"[bold green]♕ Telegram[/bold green]: [bold blue]@{__CHANNEL_USERNAME__}[/bold blue].")
    console.print("==================================================")
    console.print("[bold yellow]! Napomena[/bold yellow]: Logout pre korišćenja!.", end="\n\n")

def load_player_data(cpm):
    data = cpm.preuzmi_podatke().get('data')
    console.print("[bold][red]========[/red][ DETALJI IGRAČA ][red]========[/red][/bold]")
    console.print(f"[bold green] Name   [/bold green]: {data.get('Name', 'UNDEFINED')}")
    console.print(f"[bold green] LocalID[/bold green]: {data.get('localID', 'UNDEFINED')}")
    console.print(f"[bold green] Money  [/bold green]: {data.get('money', 'UNDEFINED')}")
    console.print(f"[bold green] Coins  [/bold green]: {data.get('coin', 'UNDEFINED')}")

def load_key_data(cpm):
    data = cpm.preuzmi_kljuc_podatke()
    console.print("[bold][red]========[/red][ DETALJI KLJUČA ][red]========[/red][/bold]")
    console.print(f"[bold green] Access Key [/bold green]: { data.get('access_key') }")
    console.print(f"[bold green] Credits    [/bold green]: { data.get('coins') }", end="\n\n")

def prompt_valid_value(content, tag, password=False):
    while True:
        value = Prompt.ask(content, password=password)
        if not value or value.isspace():
            print(f"{tag} ne može biti prazno.")
        else: return value

def rainbow_gradient_string(customer_name):
    # Logika za generisanje rainbow koda boja
    modified_string = ""
    for char in customer_name:
        color = "{:06x}".format(random.randint(0, 0xFFFFFF))
        modified_string += f'[{color}]{char}'
    return modified_string

# ==========================================================
# GLAVNA LOGIKA (MENI SA SVIM OPCIJAMA)
# ==========================================================

if __name__ == "__main__":
    console = Console()
    signal.signal(signal.SIGINT, signal_handler)
    while True:
        banner(console)
        acc_email = prompt_valid_value("[bold]➤ Email[/bold]", "Email")
        acc_password = prompt_valid_value("[bold]➤ Password[/bold]", "Password")
        acc_key = prompt_valid_value("[bold]➤ Access Key[/bold]", "Key")
        
        cpm = AnonymoControl(acc_key)
        login_res = cpm.prijavi_se(acc_email, acc_password)
        
        if login_res != 0:
            console.print("[bold red]Greška pri prijavi![/bold red]")
            sleep(2); continue
            
        while True:
            banner(console)
            load_player_data(cpm)
            load_key_data(cpm)
            
            console.print("[bold cyan](01): Povećaj Money[/bold cyan]")
            console.print("[bold cyan](02): Povećaj Coins[/bold cyan]")
            console.print("[bold cyan](03): King Rank[/bold cyan]")
            console.print("[bold cyan](04): Promeni ID[/bold cyan]")
            console.print("[bold cyan](05): Promeni Ime[/bold cyan]")
            console.print("[bold cyan](06): Rainbow Ime[/bold cyan]")
            console.print("[bold cyan](08): Obriši Nalog[/bold cyan]")
            console.print("[bold cyan](09): Registruj Novi[/bold cyan]")
            console.print("[bold cyan](10): Obriši Prijatelje[/bold cyan]")
            console.print("[bold cyan](11): Tablice[/bold cyan]")
            console.print("[bold cyan](12): W16 Motor[/bold cyan]")
            console.print("[bold cyan](13): Sve Sirene[/bold cyan]")
            console.print("[bold red](0) : Izlaz[/bold red]", end="\n\n")
            
            service = IntPrompt.ask("[bold]➤ Izaberi uslugu[/bold]")
            
            if service == 0: sys.exit(0)
            elif service == 1:
                amount = IntPrompt.ask("➤ Iznos")
                if cpm.postavi_money(amount): console.print("[green]Uspešno[/green]")
            elif service == 2:
                amount = IntPrompt.ask("➤ Iznos")
                if cpm.postavi_coins(amount): console.print("[green]Uspešno[/green]")
            elif service == 3:
                if cpm.postavi_rang(): console.print("[green]King Rank postavljen[/green]")
            elif service == 4:
                new_id = Prompt.ask("➤ Novi ID")
                if cpm.postavi_localid(new_id): console.print("[green]ID promenjen[/green]")
            elif service == 5:
                new_name = Prompt.ask("➤ Novo Ime")
                if cpm.postavi_ime(new_name): console.print("[green]Ime promenjeno[/green]")
            elif service == 6:
                new_name = Prompt.ask("➤ Ime za Rainbow")
                if cpm.postavi_ime(rainbow_gradient_string(new_name)): console.print("[green]Rainbow Ime postavljeno[/green]")
            elif service == 8:
                if Prompt.ask("Obriši nalog?", choices=["y","n"]) == "y": cpm.obrisi_nalog(); break
            elif service == 9:
                e = Prompt.ask("Novi Email"); p = Prompt.ask("Novi Password")
                cpm.registruj_se(e, p); console.print("[green]Registrovan i prijavljen[/green]")
            elif service == 10:
                if cpm.obrisi_prijatelje(): console.print("[green]Prijatelji obrisani[/green]")
            elif service == 11:
                if cpm.postavi_tablice(): console.print("[green]Tablice dodate[/green]")
            elif service == 12:
                if cpm.otkljucaj_w16(): console.print("[green]W16 otključan[/green]")
            elif service == 13:
                if cpm.otkljucaj_sirene(): console.print("[green]Sirene otključane[/green]")
            
            sleep(2)
