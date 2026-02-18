#!/usr/bin/env python3
"""
Integration Status Checker
Tests all external service connections
"""

import os
from dotenv import load_dotenv

load_dotenv()

def test_gmail():
    """Check Gmail integration"""
    from pathlib import Path
    creds_file = Path("credentials.json")
    token_file = Path("token.pickle")
    status = "✅ Connected" if (creds_file.exists() and token_file.exists()) else "❌ Not Connected"
    print(f"Gmail: {status}")
    return creds_file.exists() and token_file.exists()

def test_facebook():
    """Check Facebook integration"""
    token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
    page_id = os.getenv("FACEBOOK_PAGE_ID")
    status = "✅ Connected" if (token and page_id) else "❌ Not Connected"
    print(f"Facebook: {status}")
    if not token:
        print("  → Missing: FACEBOOK_PAGE_ACCESS_TOKEN")
    if not page_id:
        print("  → Missing: FACEBOOK_PAGE_ID")
    return bool(token and page_id)

def test_instagram():
    """Check Instagram integration"""
    token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    account_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")
    status = "✅ Connected" if (token and account_id) else "❌ Not Connected"
    print(f"Instagram: {status}")
    if not token:
        print("  → Missing: INSTAGRAM_ACCESS_TOKEN")
    if not account_id:
        print("  → Missing: INSTAGRAM_BUSINESS_ACCOUNT_ID")
    return bool(token and account_id)

def test_twitter():
    """Check Twitter integration"""
    api_key = os.getenv("TWITTER_API_KEY")
    api_secret = os.getenv("TWITTER_API_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_secret = os.getenv("TWITTER_ACCESS_SECRET")
    status = "✅ Connected" if all([api_key, api_secret, access_token, access_secret]) else "❌ Not Connected"
    print(f"Twitter: {status}")
    if not api_key:
        print("  → Missing: TWITTER_API_KEY")
    if not api_secret:
        print("  → Missing: TWITTER_API_SECRET")
    if not access_token:
        print("  → Missing: TWITTER_ACCESS_TOKEN")
    if not access_secret:
        print("  → Missing: TWITTER_ACCESS_SECRET")
    return bool(api_key and api_secret and access_token and access_secret)

def test_linkedin():
    """Check LinkedIn integration"""
    token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    client_id = os.getenv("LINKEDIN_CLIENT_ID")
    status = "✅ Connected" if (token and client_id) else "❌ Not Connected"
    print(f"LinkedIn: {status}")
    if not token:
        print("  → Missing: LINKEDIN_ACCESS_TOKEN")
    if not client_id:
        print("  → Missing: LINKEDIN_CLIENT_ID")
    return bool(token and client_id)

def test_whatsapp():
    """Check WhatsApp integration"""
    phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    status = "✅ Connected" if (phone_id and token) else "❌ Not Connected"
    print(f"WhatsApp: {status}")
    if not phone_id:
        print("  → Missing: WHATSAPP_PHONE_NUMBER_ID")
    if not token:
        print("  → Missing: WHATSAPP_ACCESS_TOKEN")
    return bool(phone_id and token)

def test_odoo():
    """Check Odoo integration"""
    url = os.getenv("ODOO_URL")
    db = os.getenv("ODOO_DB")
    username = os.getenv("ODOO_USERNAME")
    password = os.getenv("ODOO_PASSWORD")
    status = "✅ Connected" if all([url, db, username, password]) else "❌ Not Connected"
    print(f"Odoo: {status}")
    if not url:
        print("  → Missing: ODOO_URL")
    if not db:
        print("  → Missing: ODOO_DB")
    if not username:
        print("  → Missing: ODOO_USERNAME")
    if not password:
        print("  → Missing: ODOO_PASSWORD")
    return bool(url and db and username and password)

def main():
    """Run all integration tests"""
    print("=" * 60)
    print("Digital FTE - Integration Status Check")
    print("=" * 60)
    print()
    
    results = {
        "Gmail": test_gmail(),
        "Facebook": test_facebook(),
        "Instagram": test_instagram(),
        "Twitter": test_twitter(),
        "LinkedIn": test_linkedin(),
        "WhatsApp": test_whatsapp(),
        "Odoo": test_odoo()
    }
    
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    
    connected = sum(results.values())
    total = len(results)
    
    print(f"Connected: {connected}/{total}")
    print(f"Progress: {(connected/total)*100:.1f}%")
    print()
    
    if connected == total:
        print("✅ All integrations connected! Ready for Gold Tier.")
    else:
        print("⚠️  Some integrations missing. Check implementation_plan.md for setup instructions.")
        print()
        print("Priority Setup Order:")
        if not results["Odoo"]:
            print("  1. Odoo (CRITICAL for Gold Tier)")
        if not results["Facebook"]:
            print("  2. Facebook (HIGH priority)")
        if not results["Instagram"]:
            print("  3. Instagram (HIGH priority)")
        if not results["Twitter"]:
            print("  4. Twitter (HIGH priority)")
        if not results["WhatsApp"]:
            print("  5. WhatsApp (HIGH priority)")
        if not results["LinkedIn"]:
            print("  6. LinkedIn (MEDIUM priority)")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
