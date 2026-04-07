from __future__ import annotations


def build_runtime_probe_script(max_elements: int) -> str:
    return f"""
() => {{
  const maxElements = {max_elements};

  function selectorFor(el) {{
    if (el.id) {{
      return `#${{el.id}}`;
    }}
    const parts = [];
    let current = el;
    while (current && current.nodeType === 1 && parts.length < 6) {{
      let part = current.tagName.toLowerCase();
      if (current.classList && current.classList.length > 0) {{
        part += "." + Array.from(current.classList).slice(0, 2).join(".");
      }}
      parts.unshift(part);
      current = current.parentElement;
    }}
    return parts.join(" > ");
  }}

  function isVisible(el) {{
    const style = window.getComputedStyle(el);
    if (style.display === "none" || style.visibility === "hidden" || style.opacity === "0") {{
      return false;
    }}
    const rect = el.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  }}

  function belongsToIgnoredUi(el) {{
    const ignoredTokens = [
      "onetrust",
      "ot-sdk",
      "trustarc",
      "cookiebot",
      "usercentrics",
      "didomi",
      "cookieyes",
      "cookie-banner",
      "consent-banner"
    ];
    let current = el;
    while (current && current.nodeType === 1) {{
      const idValue = (current.id || "").toLowerCase();
      const classValue = (current.className || "").toString().toLowerCase();
      const roleValue = (current.getAttribute("role") || "").toLowerCase();
      const labelValue = (
        current.getAttribute("aria-label") ||
        current.getAttribute("aria-describedby") ||
        ""
      ).toLowerCase();
      if (
        ignoredTokens.some((token) => idValue.includes(token) || classValue.includes(token)) ||
        roleValue === "dialog" ||
        current.getAttribute("aria-modal") === "true" ||
        labelValue.includes("cookie") ||
        labelValue.includes("consent")
      ) {{
        return true;
      }}
      current = current.parentElement;
    }}
    return false;
  }}

  function collectElements() {{
    const seen = new Map();
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let currentId = 0;
    while (walker.nextNode()) {{
      const node = walker.currentNode;
      const rawText = (node.nodeValue || "").replace(/\\s+/g, " ").trim();
      if (!rawText) {{
        continue;
      }}
      const element = node.parentElement;
      if (!element || !isVisible(element)) {{
        continue;
      }}
      if (belongsToIgnoredUi(element)) {{
        continue;
      }}
      if (["SCRIPT", "STYLE", "NOSCRIPT"].includes(element.tagName)) {{
        continue;
      }}
      let auditId = element.getAttribute("data-font-audit-id");
      if (!auditId) {{
        currentId += 1;
        auditId = `fa-${{currentId}}`;
        element.setAttribute("data-font-audit-id", auditId);
      }}
      if (seen.has(auditId)) {{
        continue;
      }}
      const rect = element.getBoundingClientRect();
      const computed = window.getComputedStyle(element);
      seen.set(auditId, {{
        audit_id: auditId,
        selector: selectorFor(element),
        text: rawText.slice(0, 240),
        font_family: computed.fontFamily,
        font_weight: String(computed.fontWeight),
        font_style: computed.fontStyle,
        inline_style: element.getAttribute("style"),
        tag_name: element.tagName.toLowerCase(),
        class_names: Array.from(element.classList || []),
        id_attribute: element.id || null,
        bounding_box: {{
          x: rect.x + window.scrollX,
          y: rect.y + window.scrollY,
          width: rect.width,
          height: rect.height
        }}
      }});
      if (seen.size >= maxElements) {{
        break;
      }}
    }}
    return Array.from(seen.values());
  }}

  function collectFontFaceRules() {{
    const results = [];
    for (const sheet of Array.from(document.styleSheets)) {{
      let rules;
      try {{
        rules = sheet.cssRules;
      }} catch (_error) {{
        continue;
      }}
      if (!rules) {{
        continue;
      }}
      for (const rule of Array.from(rules)) {{
        if (rule.type !== CSSRule.FONT_FACE_RULE) {{
          continue;
        }}
        const src = rule.style.getPropertyValue("src") || "";
        const family = rule.style.getPropertyValue("font-family") || "";
        const urls = Array.from(src.matchAll(/url\\(([^)]+)\\)/g)).map((match) =>
          match[1].replace(/^['"]|['"]$/g, "").trim()
        );
        const sameOriginUrls = [];
        let hasLocalUrl = false;
        for (const rawUrl of urls) {{
          if (rawUrl.startsWith("data:")) {{
            continue;
          }}
          try {{
            const resolved = new URL(rawUrl, sheet.href || document.location.href);
            if (resolved.origin === document.location.origin) {{
              sameOriginUrls.push(resolved.toString());
              hasLocalUrl = true;
            }}
          }} catch (_error) {{
            hasLocalUrl = true;
            sameOriginUrls.push(rawUrl);
          }}
        }}
        results.push({{
          font_family: family.replace(/^['"]|['"]$/g, "").trim(),
          src,
          stylesheet_url: sheet.href || null,
          source_kind: sheet.href ? "linked" : "inline",
          urls,
          has_data_uri: src.includes("data:"),
          has_local_url: hasLocalUrl,
          same_origin_urls: sameOriginUrls
        }});
      }}
    }}
    return results;
  }}

  return {{
    elements: collectElements(),
    font_faces: collectFontFaceRules()
  }};
}}
"""
