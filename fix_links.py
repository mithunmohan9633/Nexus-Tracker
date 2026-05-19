
import re
import os

files = [
    ('templates/dashboard_fa.html', r'<td style="color:var\(--text-primary\); font-weight:500;">\{\{ t.title \}\}<\/td>', r'<td><a href="{% url \'ticket_detail\' t.pk %}" style="color:var(--text-primary); font-weight:500; text-decoration:none;">{{ t.title }}</a></td>'),
    ('templates/dashboard_dev.html', r'<td style="font-weight:500; color:var\(--text-primary\);">\{\{ t.title \}\}<\/td>', r'<td style="font-weight:500;"><a href="{% url \'ticket_detail\' t.pk %}" style="color:var(--text-primary); text-decoration:none;">{{ t.title }}</a></td>')
]

for filepath, pattern, repl in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        data = f.read()
    new_data = re.sub(pattern, repl, data)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_data)
print('Done!')

