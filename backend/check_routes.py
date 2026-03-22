"""
Quick route checker - Lists all registered Flask routes
"""

from app import create_app

app = create_app()

print("\n" + "="*60)
print("📋 REGISTERED ROUTES IN YOUR FLASK APP")
print("="*60 + "\n")

routes = []
for rule in app.url_map.iter_rules():
    routes.append({
        'endpoint': rule.endpoint,
        'methods': ', '.join(rule.methods - {'HEAD', 'OPTIONS'}),
        'path': str(rule)
    })

# Sort by path
routes.sort(key=lambda x: x['path'])

for route in routes:
    if route['endpoint'] != 'static':
        print(f"✓ {route['path']:<40} [{route['methods']}]")

print("\n" + "="*60)
print(f"Total routes: {len(routes)}")
print("="*60 + "\n")

# Check specifically for our new route
query_with_charts = [r for r in routes if 'query-with-charts' in r['path']]
if query_with_charts:
    print("✅ /api/query-with-charts route is REGISTERED!")
else:
    print("❌ /api/query-with-charts route is NOT FOUND!")
    print("\nTroubleshooting:")
    print("1. Check if query.py has the @query_bp.route('/query-with-charts') decorator")
    print("2. Verify the blueprint is imported in __init__.py")
    print("3. Make sure you restarted the Flask server")
