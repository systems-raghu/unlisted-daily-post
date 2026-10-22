import os
import sys
import smtplib
import html
import re
from email.message import EmailMessage
from datetime import datetime
import pytz
import requests

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

MODELS = [
    "minimax/minimax-m3.1-flash:free",
    "liquid/lfm-2.5-2.6b:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "recursive/flint-v1.0:free",
    "nvidia/nemotron-3.5-lightning:free",
    "openrouter/free"
]

NICHES = [
    {
        "category": "B2B Marketing & Agencies",
        "niche": "Performance Agencies Pitching Aesthetic & Dental Clinics",
        "target_audience": "Agency founders who run Meta/Google ads for dentists, dermatologists, and hair transplant clinics.",
        "cities": "South Delhi, Bandra & Juhu (Mumbai), Jubilee Hills (Hyderabad)",
        "pain_point": "Sales reps spend 4 hours a day on Google Maps only to get blocked by clinic receptionists who say 'doctor is in surgery'.",
        "ticket": "₹50,000 to ₹1,50,000/mo retainer per clinic"
    },
    {
        "category": "B2B High-Ticket Services",
        "niche": "Turnkey Interior Fitout & Commercial Architecture Firms",
        "target_audience": "Founders of commercial interior studios and architectural firms pitching retail stores, offices, and upscale clinics.",
        "cities": "Indiranagar & Whitefield (Bengaluru), BKC & Lower Parel (Mumbai), Gurugram",
        "pain_point": "Instagram DMs are handled by junior social media interns who delete pitches. Principal architects live on WhatsApp on-site managing contractors.",
        "ticket": "₹10L to ₹50L+ project budgets"
    },
    {
        "category": "C2B Creators & Solo Operators",
        "niche": "High-Intent UGC Creators & Video Ad Specialists Pitching D2C Brands",
        "target_audience": "Solo UGC creators, video editors, and creative strategists pitching direct-to-consumer (D2C) brands for paid ad creative.",
        "cities": "Bengaluru, Mumbai, Surat, Ahmedabad",
        "pain_point": "Cold DMs to brand Instagram pages get answered by 20-year-old community managers with zero hiring budget. Founders check WhatsApp between warehouse and ad checks.",
        "ticket": "₹30,000 to ₹1,00,000 creative retainer packages"
    },
    {
        "category": "B2B Agencies & Tech",
        "niche": "E-commerce Growth & Retention Agencies for D2C Brands",
        "target_audience": "Performance agency founders pitching high-growth consumer brands doing ₹10L–₹50L/mo GMV.",
        "cities": "Bengaluru, Mumbai, Delhi NCR, Ahmedabad",
        "pain_point": "Apollo and LinkedIn have generic info@ emails. DMs get buried in customer support. Founders review WhatsApp in between inventory and ad checks.",
        "ticket": "₹75,000 to ₹2,50,000/mo retainer"
    },
    {
        "category": "B2B Real Estate & Broking",
        "niche": "Commercial Real Estate Channel Partners & Luxury Mandate Brokers",
        "target_audience": "Agency operators and prime real estate brokers pitching luxury developers and commercial landlords.",
        "cities": "BKC (Mumbai), Golf Course Road (Gurugram), HITEC City (Hyderabad)",
        "pain_point": "Portals sell recycled 2-year-old lead lists to 500 brokers. Agency pitches must hit the managing partner or prime broker directly on WhatsApp.",
        "ticket": "₹2Cr to ₹15Cr property mandates"
    },
    {
        "category": "B2B Creative Studios",
        "niche": "High-End Video Production & Commercial Studios",
        "target_audience": "Creative directors and video production house founders pitching corporate commercials and D2C brand films.",
        "cities": "Mumbai, Bengaluru, Delhi NCR",
        "pain_point": "Cold emails bounce or sit in unread agency inboxes. Brand CMOs and founders respond to 15-second personalized video reviews on WhatsApp.",
        "ticket": "₹1,50,000 to ₹6,00,000 per brand film"
    },
    {
        "category": "B2B Industrial & Manufacturing",
        "niche": "B2B Industrial, Capital Equipment & Solar EPC Contractors",
        "target_audience": "Marketing leaders and sales heads of industrial machinery manufacturers and commercial solar installers.",
        "cities": "Pune, Coimbatore, Peenya (Bengaluru), Ahmedabad",
        "pain_point": "Cold emails get flagged as spam. Managing Directors never check LinkedIn InMail, but keep WhatsApp open all day for client purchase orders.",
        "ticket": "₹15L to ₹1Cr+ industrial orders"
    },
    {
        "category": "C2B High-Ticket Freelancers",
        "niche": "Direct-Response Copywriters & Funnel Builders Pitching E-comm Founders",
        "target_audience": "Solo direct-response copywriters, email marketing specialists, and funnel consultants.",
        "cities": "National / Remote (India & Global)",
        "pain_point": "Cold emails to generic support desks never reach the founder. A 3-line WhatsApp teardown identifying an email checkout leak gets answered in 10 minutes.",
        "ticket": "₹40,000 to ₹1,20,000/mo retainer"
    },
    {
        "category": "B2B Consulting & HR",
        "niche": "Corporate Training, Executive Coaching & HR Consultancies",
        "target_audience": "Founders of leadership training consultancies and boutique executive search firms pitching fast-scaling startups.",
        "cities": "Bengaluru, Delhi NCR, Hyderabad, Mumbai",
        "pain_point": "Pitches to corporate HR land in a black hole. Founders need direct mobile access to the CEO or COO.",
        "ticket": "₹1,50,000 to ₹5,00,000 per engagement"
    },
    {
        "category": "B2B Hospitality & Retail",
        "niche": "Fine-Dining, Cloud Kitchen & Franchise Restaurant Chains",
        "target_audience": "Agency founders pitching food & beverage brand scaling, local SEO, and influencer marketing.",
        "cities": "Koramangala (Bengaluru), Connaught Place (Delhi), Indiranagar",
        "pain_point": "On-site restaurant managers never pass sales calls to the owner. The owner only monitors daily revenue and supplier chats on WhatsApp.",
        "ticket": "₹1L to ₹3L/mo marketing/growth retainers"
    }
]

def get_daily_niche(dt=None):
    """Deterministically pick today's high-ticket Indian B2B or C2B niche based on day of year."""
    if dt is None:
        tz = pytz.timezone("Asia/Kolkata")
        dt = datetime.now(tz)
    idx = dt.timetuple().tm_yday % len(NICHES)
    return NICHES[idx]

def build_prompt(niche_info):
    return f"""You are the Chief Marketing Officer and Growth Lead for 'Unlisted' (the B2B WhatsApp decision-maker lead engine in India).
Generate today's complete Daily Marketing Brief & Growth Stack for the founder (Ram) to market Unlisted and acquire paying agency and B2B clients.

TODAY'S TARGET FOCUS:
- Category: {niche_info['category']}
- Niche: {niche_info['niche']}
- Target Audience: {niche_info['target_audience']}
- Target Cities: {niche_info['cities']}
- Friction & Gatekeeper Bottleneck: {niche_info['pain_point']}
- Average Deal Size: {niche_info['ticket']}

THE PRODUCT (UNLISTED):
- What it does: Crawls live business websites to extract verified business owner WhatsApp numbers directly.
- Core Advantages:
  * 100% Ban-Proof: Zero bots or automation touching their WhatsApp accounts. Human reps tap a pre-filled 1-click wa.me link to send.
  * Zero Passwords or Logins Required: Never ask for Instagram, WhatsApp, or email logins (0% account liability).
  * Fresh, Active Data: Pulled directly from live business websites and active domains, never stale or recycled databases.
- Economic Anchor: Replaces a ₹25,000–₹35,000/mo junior SDR for ₹8,000/mo flat.
- Risk-Reversal Offer: "Test on your niche 2 weeks free. If it books meetings, pay ₹8,000. If not, ₹0 and keep the leads."

IMPORTANT TONE & JARGON RULE:
- DO NOT mention legal acts or compliance statutes (NO "DPDP Act", NO "Section 3(c)(ii)"). Buyers don't care about legal jargon—they care about: ban-proof safety, zero password requests, and direct owner WhatsApp numbers that actually reply.

OUTPUT FORMAT (You must output EXACTLY the following 4 labeled sections using these exact headers):

=== 1. TODAY'S DIRECTIVE & GROWTH STACK ===
- 3 clear bullet points: Step-by-step instructions for Ram on what to execute today in 15 minutes.
- Psychology Lever: 1 sentence explaining the psychological trigger used today (from consumer psychology or business economics).
- Daily Book Takeaway: Exactly 1 actionable insight from a classic book (Influence by Cialdini, Never Split the Difference by Chris Voss, $100M Offers by Alex Hormozi, Alchemy by Rory Sutherland, The Ultimate Sales Machine by Chet Holmes, Thinking Fast and Slow by Daniel Kahneman, Pitch Anything by Oren Klaff). Format: 📖 *[Book Name] by [Author]:* "[Quote/Concept] — [Application]"

=== 2. WHATSAPP COMMUNITY POST ===
- High-converting post ready to paste into WhatsApp founder and agency groups.
- Punchy pattern interrupt exposing why outreach fails for {niche_info['niche']}.
- 2-3 lines of practical sales strategy.
- Seamless bridge to Unlisted (verified owner WhatsApp numbers, 1-tap wa.me, 100% ban-proof, zero password requests).
- ₹8,000 vs ₹0 risk reversal + CTA: "Drop your target niche + city below to test 2 weeks free."
- WhatsApp formatting (*bold*, blank lines between sentences). NO corporate jargon. NO day-of-week mentions. 130-180 words.

=== 3. LINKEDIN AUTHORITY POST ===
- Compelling scroll-stopping 2-line hook.
- A hard-hitting breakdown of why Indian agencies waste money on SDRs cold-calling receptionists or sending dead emails.
- Contrast table or bullet points comparing Old Outbound (Apollo/IG scrapers/calls) vs New Outbound (Direct WhatsApp + Ban-Proof 1-tap wa.me).
- Offer & CTA: "Want to test this? Comment 'DATA' and your city below — I'll send you 10 verified owner WhatsApp lines for your niche 100% free."
- 150-220 words. Clean LinkedIn formatting.

=== 4. DIRECT OUTBOUND TROJAN HORSE PITCH ===
- A 1-to-1 cold WhatsApp message Ram can send directly to 5 agency founders who serve {niche_info['niche']}.
- Permissionless value: "Hey [Name], ran a live scan across [City] and pulled 3 verified clinic/business owner WhatsApp direct lines this morning: [Lead 1, Lead 2, Lead 3]. Have 30 more in a sheet. Free to test if your team wants?"
- Under 90 words. Zero pitch, 100% value.
"""

def parse_sections(raw_text):
    sections = {
        "directive": "",
        "whatsapp": "",
        "linkedin": "",
        "trojan": ""
    }
    headers = re.findall(r'===\s*([^=\n]+)\s*===', raw_text)
    bodies = re.split(r'===\s*[^=\n]+\s*===', raw_text)[1:]

    for h, b in zip(headers, bodies):
        h_lower = h.lower()
        b_clean = b.strip()
        if "directive" in h_lower or "growth stack" in h_lower:
            sections["directive"] = b_clean
        elif "whatsapp" in h_lower:
            sections["whatsapp"] = b_clean
        elif "linkedin" in h_lower:
            sections["linkedin"] = b_clean
        elif "trojan" in h_lower or "outbound" in h_lower:
            sections["trojan"] = b_clean

    if not sections["whatsapp"] and not sections["linkedin"]:
        sections["whatsapp"] = raw_text.strip()

    return sections

def build_html_email(niche_info, raw_text):
    sections = parse_sections(raw_text)

    directive_html = html.escape(sections["directive"]).replace("\n", "<br>")
    whatsapp_html = html.escape(sections["whatsapp"]).replace("\n", "<br>")
    linkedin_html = html.escape(sections["linkedin"]).replace("\n", "<br>")
    trojan_html = html.escape(sections["trojan"]).replace("\n", "<br>")

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Daily Marketing Brief</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }}
  .container {{ max-width: 680px; margin: 0 auto; }}
  .header {{ background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border: 1px solid #334155; border-radius: 12px; padding: 24px; margin-bottom: 20px; }}
  .badge {{ display: inline-block; padding: 4px 10px; border-radius: 9999px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; }}
  .badge-category {{ background: #3b82f6; color: #ffffff; }}
  .badge-city {{ background: #334155; color: #94a3b8; margin-left: 6px; }}
  h1 {{ font-size: 20px; font-weight: 700; margin: 0 0 8px 0; color: #ffffff; }}
  .card {{ background: #1e293b; border-radius: 12px; padding: 20px; margin-bottom: 20px; border: 1px solid #334155; }}
  .card-header {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; border-bottom: 1px solid #334155; padding-bottom: 10px; }}
  .card-title {{ font-size: 14px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; display: flex; align-items: center; gap: 8px; }}
  .whatsapp-title {{ color: #25D366; }}
  .linkedin-title {{ color: #38bdf8; }}
  .trojan-title {{ color: #f59e0b; }}
  .directive-title {{ color: #a855f7; }}
  .copy-block {{ background: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 16px; font-family: -apple-system, BlinkMacSystemFont, monospace, sans-serif; font-size: 13px; line-height: 1.6; color: #e2e8f0; white-space: pre-wrap; word-break: break-word; user-select: all; }}
  .meta-info {{ font-size: 12px; color: #94a3b8; line-height: 1.5; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <span class="badge badge-category">{html.escape(niche_info.get('category', 'B2B Outbound'))}</span>
    <span class="badge badge-city">{html.escape(niche_info.get('cities', 'India'))}</span>
    <h1>Today's Target: {html.escape(niche_info.get('niche', 'B2B Niche'))}</h1>
    <div class="meta-info">Deal Size: {html.escape(niche_info.get('ticket', '₹50k-₹2L'))} • Replaces a ₹25k-₹35k/mo SDR for ₹8,000/mo flat</div>
  </div>

  <div class="card">
    <div class="card-header">
      <div class="card-title directive-title">🎯 1. Today's 15-Minute Directive & Growth Stack</div>
    </div>
    <div style="font-size: 13px; line-height: 1.6; color: #cbd5e1;">
      {directive_html}
    </div>
  </div>

  <div class="card">
    <div class="card-header">
      <div class="card-title whatsapp-title">📱 2. WhatsApp Community & Group Post (Tap to Copy)</div>
    </div>
    <div class="copy-block">{whatsapp_html}</div>
  </div>

  <div class="card">
    <div class="card-header">
      <div class="card-title linkedin-title">💼 3. LinkedIn Authority Post (Tap to Copy)</div>
    </div>
    <div class="copy-block">{linkedin_html}</div>
  </div>

  <div class="card">
    <div class="card-header">
      <div class="card-title trojan-title">⚔️ 4. Direct Outbound Trojan Horse Pitch (Send to 5 Agency Founders)</div>
    </div>
    <div class="copy-block">{trojan_html}</div>
  </div>
</div>
</body>
</html>"""

def draft_post(niche_info=None):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENROUTER_API_KEY environment variable")

    if niche_info is None:
        niche_info = get_daily_niche()

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://github.com/busywithram-blip/unlisted-daily-post",
        "X-Title": "Unlisted Daily Post",
        "Content-Type": "application/json"
    }

    prompt = build_prompt(niche_info)

    errors = []
    for model in MODELS:
        try:
            r = requests.post(url, headers=headers, json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 3000,
                "temperature": 0.7
            }, timeout=45)
            if r.status_code == 200:
                data = r.json()
                if "choices" in data and len(data["choices"]) > 0:
                    choice = data["choices"][0]
                    content = choice.get("message", {}).get("content")
                    if content and content.strip():
                        return content.strip()
                    finish_reason = choice.get("finish_reason")
                    errors.append(f"{model}: HTTP 200 but empty content (finish_reason: {finish_reason})")
                else:
                    errors.append(f"{model}: HTTP 200 but no choices returned")
            else:
                errors.append(f"{model}: HTTP {r.status_code} - {r.text[:120]}")
        except Exception as e:
            errors.append(f"{model}: {e}")

    raise RuntimeError(f"All model attempts failed: {'; '.join(errors)}")

def send_email(content, niche_info=None, subject=None):
    user = os.environ.get("GMAIL_USER", "busywithram@gmail.com")
    pwd  = os.environ.get("GMAIL_APP_PASSWORD", "tuavhrwqahthbkcj")

    if niche_info is None:
        niche_info = get_daily_niche()

    to_emails_raw = os.environ.get("TO_EMAILS", user)
    recipients = [e.strip() for e in to_emails_raw.split(",") if e.strip()]
    if not recipients:
        recipients = [user]

    if subject is None:
        subject = f"🔥 Daily Marketing Brief & Growth Stack: {niche_info['niche']}"

    msg = EmailMessage()
    msg["From"] = user
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject

    # Plain text version
    msg.set_content(content)

    # HTML rich card version
    html_content = build_html_email(niche_info, content)
    msg.add_alternative(html_content, subtype="html")

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as s:
            s.starttls()
            s.login(user, pwd)
            s.send_message(msg)
        return "ok"
    except Exception as e:
        raise RuntimeError(f"Failed to send email: {e}")

if __name__ == "__main__":
    niche = get_daily_niche()
    post = draft_post(niche)
    status = send_email(post, niche_info=niche)
    print(status)
