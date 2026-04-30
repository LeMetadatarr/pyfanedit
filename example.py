from pyfanedit import FaneditClient

client = FaneditClient()

# Search
print("=== Search: batman ===")
results, next_page = client.search("batman")
for r in results[:5]:
    print(f"  [{r.fanedit_type}] {r.title} by {r.faneditor} ({r.release_date})")
    print(f"    {r.url}")
print(f"  ... {len(results)} results, next page: {next_page}")

# Category browsing
print("\n=== FanFix category (page 1) ===")
items, _ = client.get_category("fanfix")
for item in items[:5]:
    print(f"  {item.title} | editor={item.editor_rating} user={item.user_rating}")

# Franchise tag
print("\n=== Star Wars franchise ===")
sw, _ = client.get_by_tag("franchise", "star-wars")
for item in sw[:5]:
    print(f"  {item.title}")

# Detail page
print("\n=== Detail: first result ===")
if results:
    detail = client.get_detail(results[0].url)
    print(f"  Title: {detail.title}")
    print(f"  Genre: {detail.genre}")
    print(f"  Original: {detail.original_title} ({detail.original_release_date})")
    print(f"  Type: {detail.fanedit_type}")
    print(f"  Runtime: {detail.fanedit_running_time}")
    print(f"  Synopsis: {(detail.synopsis or '')[:200]}")
