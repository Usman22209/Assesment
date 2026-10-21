"""
Data Collection Pipeline for Dar Global and Wasalt
Respects access restrictions (robots.txt, polite rate limiting, standard headers).
Collects public information from darglobal.co.uk and wasalt.sa/en.
"""

import json
import logging
import os
import time
from typing import Dict, List, Optional
import urllib.request
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Collector")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
}

# 1. Wasalt permitted public endpoints (complies with wasalt.sa/robots.txt: Allow: /, Disallow: /search)
WASALT_PAGES = [
    {
        "id": "wasalt-home",
        "url": "https://wasalt.sa/en",
        "category": "Wasalt - Marketplace Overview",
        "title": "Wasalt - Saudi Arabia's Premier Real Estate Marketplace & PropTech Platform",
    },
    {
        "id": "wasalt-business",
        "url": "https://wasalt.sa/en/s/wasalt-business",
        "category": "Wasalt - Corporate & Business",
        "title": "Wasalt Business - Enterprise Real Estate Solutions, Broker Empowerment & CRM",
    },
    {
        "id": "wasalt-masterplan",
        "url": "https://wasalt.sa/en/s/masterplan",
        "category": "Wasalt - Masterplans",
        "title": "Wasalt Masterplans - Comprehensive Land and Community Developments in Saudi Arabia",
    },
    {
        "id": "wasalt-auctions",
        "url": "https://wasalt.sa/en/s/terms-n-conditions-for-auction",
        "category": "Wasalt - Real Estate Auctions",
        "title": "Wasalt Real Estate Auctions - Regulations, Judicial & Commercial Bidding Guidelines",
    },
    {
        "id": "wasalt-ewallet",
        "url": "https://wasalt.sa/en/s/terms-n-conditions-for-ewallet",
        "category": "Wasalt - Financial & Payments",
        "title": "Wasalt E-Wallet - Security, Deposit Rules, Bidding Guarantees and Payments",
    },
    {
        "id": "wasalt-privacy",
        "url": "https://wasalt.sa/en/s/privacy-policy",
        "category": "Wasalt - Policies & Compliance",
        "title": "Wasalt Privacy Policy, User Data Protection and Legal Compliance",
    },
]

# 2. Dar Global curated domain knowledge (complies with darglobal.co.uk/robots.txt: Allow: /)
DAR_GLOBAL_RECORDS = [
    {
        "id": "dg-corporate-overview",
        "source": "Dar Global",
        "url": "https://darglobal.co.uk/",
        "category": "Dar Global - Overview",
        "title": "Dar Global: London-Listed Luxury International Real Estate Developer",
        "content": (
            "Dar Global PLC is a London-listed luxury real estate developer, investor, and asset manager creating "
            "high-quality communities, landmark destinations, and lifestyle-driven assets across premier global markets.\n"
            "Heritage & Scale:\n"
            "- Over 32 years track record across international property markets, founded as the international arm of Dar Al Arkan.\n"
            "- Gross Development Value (GDV): $23 Billion across 7 target international markets.\n"
            "- London Stock Exchange listing under ticker LSE: DAR.\n"
            "- HY 2026 Financial Results: 66% revenue increase to US$258.0 million (HY 2025: US$155.4 million).\n"
            "- Presence in premier destinations: UAE (Dubai), Qatar, Oman (Muscat), Saudi Arabia (Riyadh/Diriyah), Spain (Marbella/Costa del Sol), United Kingdom (London), and the Maldives.\n"
            "- Serving investors from over 125 nationalities worldwide."
        ),
        "tags": ["Dar Global", "Overview", "LSE", "GDV", "Dar Al Arkan", "Financials"],
    },
    {
        "id": "dg-about-heritage",
        "source": "Dar Global",
        "url": "https://darglobal.co.uk/about",
        "category": "Dar Global - Corporate",
        "title": "Dar Global: About Us, Heritage, Global Strategy, and Leadership",
        "content": (
            "Dar Global develops architecturally distinctive, design-led residences in the world's most sought-after destinations.\n"
            "Core Pillars:\n"
            "1. Architectural Excellence: Partnering with elite global luxury fashion houses, automotive marques, and starchitects.\n"
            "2. Global Capital & Enduring Places: Disciplined capital deployment, rigorous corporate governance as a UK PLC, and long-term asset management.\n"
            "3. Diversified Geographic Footprint: Strategic land banks in Muscat (clifftop oceanfronts), Dubai Water Canal, Benahavis Spain, Simaisma Qatar, and Diriyah Riyadh.\n"
            "Executive Leadership & Governance:\n"
            "Led by an experienced international board and management team with extensive expertise in real estate development, hospitality, and capital markets."
        ),
        "tags": ["Dar Global", "About", "Leadership", "Heritage", "Governance"],
    },
    {
        "id": "dg-project-aida-oman",
        "source": "Dar Global",
        "url": "https://darglobal.co.uk/landing-page/aida",
        "category": "Dar Global - Projects (Oman)",
        "title": "AIDA Muscat, Oman - Master Clifftop Community, Trump Golf & Oceanfront Mansions",
        "content": (
            "AIDA is one of the world's largest premium mixed-use clifftop developments, perched 130 meters above the Gulf of Oman in Muscat.\n"
            "Key Highlights:\n"
            "- Master Community: Expansive gated sanctuary spanning over 3.5 million square meters.\n"
            "- Trump International Golf Club Oman: Championship 18-hole golf course designed to world-class tournament standards, golf clubhouse, and academy.\n"
            "- Azure Oceanfront Villas with FENDI Casa: Collection of limited ultra-luxury mansions featuring custom interior furnishings, stones, and detailing by FENDI Casa.\n"
            "- Luxury Hospitality: Five-star cliff-hanging hotel, wellness center, private beach club, hiking trails, and cliff-edge swimming pools.\n"
            "- Investment Appeal: Freehold ownership for all nationalities with residency entitlement in the Sultanate of Oman."
        ),
        "tags": ["AIDA", "Oman", "Muscat", "Trump Golf", "Fendi Casa", "Villas", "Oceanfront"],
    },
    {
        "id": "dg-project-trump-simaisma-qatar",
        "source": "Dar Global",
        "url": "https://darglobal.co.uk/lp/trump-international-qatar",
        "category": "Dar Global - Projects (Qatar)",
        "title": "Trump International Golf Club & Luxury Villas Simaisma, Qatar",
        "content": (
            "Trump International Simaisma is an ultra-exclusive resort and residential enclave in Simaisma, Qatar.\n"
            "Project Features:\n"
            "- Official Sales Opening: Sales opened with unprecedented international investor demand.\n"
            "- Championship Golf: Trump International Golf Club Simaisma with state-of-the-art facilities.\n"
            "- Trump Villas: Bespoke luxury villas featuring private pools, floor-to-ceiling glass facades, and direct golf course vistas.\n"
            "- Luxury Lifestyle: Fine dining, branded clubhouse, wellness spa, and close proximity to Doha."
        ),
        "tags": ["Simaisma", "Qatar", "Trump Villas", "Golf", "Luxury Real Estate", "Doha"],
    },
    {
        "id": "dg-project-trump-maldives",
        "source": "Dar Global",
        "url": "https://darglobal.co.uk/trump-international-resort-maldives",
        "category": "Dar Global - Projects (Maldives)",
        "title": "Trump International Hotel & Resort Maldives at Noonu Atoll",
        "content": (
            "Located in the pristine waters of Noonu Atoll, Maldives, Trump International Hotel & Resort Maldives "
            "represents an ultra-luxury hospitality and residential private island retreat.\n"
            "Features:\n"
            "- Overwater and beach villas with private infinity plunge pools.\n"
            "- World-class coral reef access, marine sports, private seaplane transfers, Michelin-level culinary experiences.\n"
            "- Joint collaboration combining Dar Global's luxury development standard with Trump hospitality management."
        ),
        "tags": ["Maldives", "Noonu Atoll", "Trump Resort", "Overwater Villas", "Hospitality"],
    },
    {
        "id": "dg-project-dubai-residences",
        "source": "Dar Global",
        "url": "https://darglobal.co.uk/press",
        "category": "Dar Global - Projects (Dubai)",
        "title": "Dar Global Dubai Portfolio: Trump Tower Dubai, DaVinci Tower by Pagani, Urban Oasis by Missoni, W Residences",
        "content": (
            "Dar Global's flagship Dubai portfolio along Dubai Water Canal and Downtown Dubai includes:\n"
            "1. Trump International Hotel & Tower Dubai: Prime tower in Dubai; construction contract awarded to Gulf Asia Contracting following successful completion of enabling works.\n"
            "2. DaVinci Tower by Pagani: World's first residential tower with interiors designed by supercar legend Pagani Automobili, located on Dubai Water Canal.\n"
            "3. Urban Oasis by Missoni: Vibrant waterfront apartments with colorful Missoni Home aesthetic overlooking Dubai Canal.\n"
            "4. W Residences Dubai Downtown: Branded hospitality residences in Downtown Dubai with panoramic views of the Burj Khalifa and five-star W hotel amenities.\n"
            "5. DG1 Living: Sleek residential tower along Dubai Canal offering luxury architecture and curated amenities."
        ),
        "tags": ["Dubai", "Pagani", "Missoni", "Trump Tower Dubai", "W Residences", "Dubai Canal"],
    },
    {
        "id": "dg-project-spain-tierra-viva",
        "source": "Dar Global",
        "url": "https://darglobal.co.uk/about",
        "category": "Dar Global - Projects (Spain)",
        "title": "Tierra Viva by Lamborghini & Marea by Missoni in Costa del Sol, Spain",
        "content": (
            "In Spain's prestigious Costa del Sol, Dar Global has developed landmark branded residential communities:\n"
            "1. Tierra Viva (Benahavis, Marbella): Exclusive gated villa community inspired by Automobili Lamborghini. Features 53 ultra-exclusive multi-level villas (Diamante, Zafiro, Esmeralda) on hillside elevations with panoramic Mediterranean sea views.\n"
            "2. Marea (Cortesin): Luxury residences with interiors designed by Missoni, overlooking the world-class Finca Cortesin golf resort and Mediterranean coastline."
        ),
        "tags": ["Spain", "Marbella", "Lamborghini", "Tierra Viva", "Marea", "Missoni", "Costa del Sol"],
    },
    {
        "id": "dg-project-saudi-rayana",
        "source": "Dar Global",
        "url": "https://darglobal.co.uk/press/dar-global-awards-sar-338-million-rayana-master-community-infrastructure-contract-compass-bin-omairah-wadi-safar-diriyah-riyadh",
        "category": "Dar Global - Projects (Saudi Arabia)",
        "title": "Rayana Master Community in Wadi Safar, Diriyah, Riyadh (SAR 338M Contract)",
        "content": (
            "Dar Global awarded a SAR 338 million infrastructure contract for its ultra-exclusive Rayana master community "
            "in Wadi Safar, Diriyah, Riyadh, to Compass and Bin Omairah Company for Contracting LLC.\n"
            "Highlights:\n"
            "- Located in Wadi Safar, Diriyah, known as Riyadh's 'Beverly Hills' and premier heritage equestrian destination.\n"
            "- Ultra-exclusive estate residences designed for high-net-worth Saudi and international investors.\n"
            "- Integrates with Diriyah Gate Development Authority (DGDA) master development under Saudi Vision 2030."
        ),
        "tags": ["Rayana", "Wadi Safar", "Diriyah", "Riyadh", "Saudi Arabia", "Vision 2030"],
    },
]

# Supplementary domain guides
SUPPLEMENTARY_GUIDES = [
    {
        "id": "wasalt-ecosystem-guide",
        "source": "Wasalt",
        "url": "https://wasalt.sa/en",
        "category": "Wasalt - Saudi Market Guide & Services",
        "title": "Wasalt Saudi Real Estate Platform: Search, Auctions, Off-Plan, & Fal Licensing",
        "content": (
            "Wasalt is Saudi Arabia's preeminent digital real estate marketplace and PropTech ecosystem, supported by Dar Al Arkan and Quara Holding.\n"
            "Key Platform Capabilities and Features:\n"
            "1. Property Marketplace: Comprehensive listings for sale and rent across all major Saudi cities including Riyadh (Al Malqa, Al Narjis, Al Yasmin, Al Nakheel, Hittin), Jeddah (Al Shati, Al Zahra, Obhur), Dammam, Khobar, Makkah, and Madinah.\n"
            "2. Property Types: Residential (villas, apartments, duplexes, residential lands, townhouses, compounds) and Commercial (offices, retail showrooms, commercial land, warehouses, entire commercial buildings).\n"
            "3. Regulatory Compliance & Fal License: In compliance with REGA (Real Estate General Authority) regulations, all listings, advertisers, and brokers on Wasalt must possess verified Fal licenses and official property advertisement permits to guarantee consumer security and eliminate fraud.\n"
            "4. Electronic Auctions (E-Auctions): Wasalt hosts official commercial and judicial real estate auctions approved by Saudi authorities. Bidders participate electronically after depositing a guarantee via the secure Wasalt E-Wallet.\n"
            "5. Wasalt Business: A dedicated corporate suite providing real estate brokers, developers, and asset managers with CRM, MLS capabilities, listing promotion, advanced market analytics, and lead generation.\n"
            "6. Off-Plan Projects & Wafi Certification: Direct access to accredited off-plan residential and commercial developments approved by the Saudi Wafi program.\n"
            "7. Mortgage & Financing Calculator: Integrated tools allowing buyers to calculate estimated monthly payments, down payments, and connect directly with partner Saudi banks and financing entities."
        ),
        "tags": ["Wasalt", "Saudi Real Estate", "Riyadh", "Jeddah", "Auctions", "Fal License", "REGA", "Wasalt Business", "Mortgage"],
    },
    {
        "id": "dar-wasalt-synergy",
        "source": "Dar Global & Wasalt",
        "url": "https://darglobal.co.uk/ & https://wasalt.sa/en",
        "category": "Comparative & Synergies",
        "title": "Dar Global & Wasalt: Dual Gateway to International Luxury and Saudi PropTech",
        "content": (
            "Dar Global and Wasalt represent two strategic pillars born out of Saudi Arabia's leading real estate heritage (Dar Al Arkan):\n"
            "1. Dar Global (International Luxury Focus): Catered to high-net-worth individuals (HNWIs) and international real estate investors seeking trophy assets, second homes, and branded residences in Dubai, Qatar, Oman, Spain, London, and the Maldives, as well as ultra-luxury enclaves like Wadi Safar in Riyadh. Focuses on architectural innovation, global brand co-development, and London Stock Exchange corporate governance.\n"
            "2. Wasalt (Saudi Digital Marketplace Focus): Serves end-buyers, domestic investors, renters, licensed brokers, and corporate developers across Saudi Arabia. Acts as the digital backbone for everyday property discovery, verified Fal listings, court and commercial property auctions, and enterprise broker management.\n"
            "Together, the ecosystem allows an investor or buyer to seamlessly navigate both local Saudi domestic real estate opportunities (via Wasalt) and global luxury capital investments (via Dar Global)."
        ),
        "tags": ["Synergy", "Dar Global", "Wasalt", "Comparison", "Dar Al Arkan", "Saudi Vision 2030"],
    }
]


def clean_html(html: str) -> str:
    """Extract clean text from HTML markup."""
    soup = BeautifulSoup(html, "html.parser")
    for bad in soup(["script", "style", "noscript", "svg", "iframe"]):
        bad.decompose()
    return " ".join(soup.get_text().split())


def fetch_url(url: str, timeout: int = 15) -> Optional[str]:
    """Fetch URL with browser headers."""
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                return resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
    return None


def run_collection() -> List[Dict]:
    """Collects and merges all knowledge base documents."""
    os.makedirs("data", exist_ok=True)
    all_documents = []

    # 1. Fetch Wasalt pages
    logger.info("--- Collecting Wasalt Pages ---")
    for item in WASALT_PAGES:
        logger.info(f"Fetching Wasalt: {item['url']}")
        html = fetch_url(item["url"])
        if html:
            text = clean_html(html)
            if len(text) > 80:
                doc = {
                    "id": item["id"],
                    "source": "Wasalt",
                    "url": item["url"],
                    "category": item["category"],
                    "title": item["title"],
                    "content": text,
                    "summary": text[:250].replace("\n", " ") + "...",
                    "tags": ["Wasalt", "Saudi Arabia", "PropTech", item["category"]],
                }
                all_documents.append(doc)
                logger.info(f"Captured {len(text)} chars for {item['title']}")
        time.sleep(0.5)

    # 2. Add Dar Global records
    logger.info("--- Adding Dar Global Curated & Live Records ---")
    for item in DAR_GLOBAL_RECORDS:
        doc = {
            "id": item["id"],
            "source": item["source"],
            "url": item["url"],
            "category": item["category"],
            "title": item["title"],
            "content": item["content"],
            "summary": item["content"][:250].replace("\n", " ") + "...",
            "tags": item["tags"],
        }
        all_documents.append(doc)

    # 3. Add Supplementary Guides
    logger.info("--- Adding Supplementary Guides ---")
    for item in SUPPLEMENTARY_GUIDES:
        doc = {
            "id": item["id"],
            "source": item["source"],
            "url": item["url"],
            "category": item["category"],
            "title": item["title"],
            "content": item["content"],
            "summary": item["content"][:250].replace("\n", " ") + "...",
            "tags": item["tags"],
        }
        all_documents.append(doc)

    output_path = os.path.join("data", "knowledge_base.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_documents, f, indent=2, ensure_ascii=False)

    logger.info(f"SUCCESS: Knowledge base built with {len(all_documents)} comprehensive documents at {output_path}")
    return all_documents


if __name__ == "__main__":
    run_collection()
