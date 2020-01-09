#!/usr/bin/env python3

import requests
import requests_cache
import io
import cgitb
import cgi
import sys
import json
from dominate import document
from dominate.tags import *

cgitb.enable()

if hasattr(sys.stdout, "buffer"):
  def bwrite(s):
    sys.stdout.flush()
    sys.stdout.buffer.write(s)
  write = sys.stdout.write
else:
  wrapper = io.TextIOWrapper(sys.stdout)
  def bwrite(s):
    wrapper.flush()
    sys.stdout.write(s)
  write = wrapper.write

write("Content-type: text/html;charset=utf-8\r\n\r\n")


def get_books_slice(offset, limit, **kwargs):
    params = {
                   'author_weight__gte': 0,
                   'limit': limit,
                   'o': 'popular',
                   'offset': offset,
                   'type': "text",
               }
    params.update(kwargs)
    return json.loads(requests.get("https://mybook.ru/api/books/", params).content.decode("utf-8"))


def get_books(max_num, **kwargs):
    req = get_books_slice(0, 1, **kwargs)
    total = req['meta']['total_count'] if max_num == 0 else min(req['meta']['total_count'], max_num)
    bunch_size = 100
    l = []
    for i in range(total // bunch_size + (0 if total % bunch_size == 0 else 1)):
        l.extend(get_books_slice(i * bunch_size, bunch_size, **kwargs)['objects'])
        sys.stderr.write(f"\ngot {i*bunch_size + bunch_size} of {total}")
    return l[:total if max_num == 0 else max_num]


# requests_cache.install_cache('all_books_cache', backend='sqlite', expire_after=60*60*24*365)
requests_cache.install_cache('fantasy_books_cache', backend='sqlite', expire_after=60*60*24*365)

# json_res = get_books(20, **{'genres': 178})
json_res = get_books(0, **{'niches': 22})


form = cgi.FieldStorage()


def f(x, w, wo):
    sp = x['genres_names'].split(', ')
    return (not w or w in sp) and (not wo or wo not in sp)


for i in range(1, 12):
    genre_name = form.getfirst('ch' + str(i))
    genre_name_wo = form.getfirst('wo' + str(i))
    if genre_name or genre_name_wo:
        json_res = list(filter(lambda x: f(x, genre_name, genre_name_wo), json_res))


print(f"""
    <form action="/cgi-bin/main.py">
        <input type="checkbox" name="ch1" {'checked' if form.getfirst('ch1') else ''} value="Боевое фэнтези">Боевое фэнтези<br>
        <input type="checkbox" name="ch2" {'checked' if form.getfirst('ch2') else ''} value="Героическое фэнтези">Героическое фэнтези<br>
        <input type="checkbox" name="ch3" {'checked' if form.getfirst('ch3') else ''} value="Городское фэнтези">Городское фэнтези<br>
        <input type="checkbox" name="ch4" {'checked' if form.getfirst('ch4') else ''} value="Детективное фэнтези">Детективное фэнтези<br>
        <input type="checkbox" name="ch5" {'checked' if form.getfirst('ch5') else ''} value="Книги про вампиров">Книги про вампиров<br>
        <input type="checkbox" name="ch6" {'checked' if form.getfirst('ch6') else ''} value="Книги про волшебников">Книги про волшебников<br>
        <input type="checkbox" name="ch7" {'checked' if form.getfirst('ch7') else ''} value="Любовное фэнтези">Любовное фэнтези<br>
        <input type="checkbox" name="ch8" {'checked' if form.getfirst('ch8') else ''} value="Попаданцы">Попаданцы<br>
        <input type="checkbox" name="ch9" {'checked' if form.getfirst('ch9') else ''} value="Русское фэнтези">Русское фэнтези<br>
        <input type="checkbox" name="ch10" {'checked' if form.getfirst('ch10') else ''} value="Фэнтези про драконов">Фэнтези про драконов<br>
        <input type="checkbox" name="ch11" {'checked' if form.getfirst('ch11') else ''} value="Юмористическое фэнтези">Юмористическое фэнтези<br>
        <br>
        <input type="checkbox" name="wo1" {'checked' if form.getfirst('wo1') else ''} value="Боевое фэнтези">Боевое фэнтези<br>
        <input type="checkbox" name="wo2" {'checked' if form.getfirst('wo2') else ''} value="Героическое фэнтези">Героическое фэнтези<br>
        <input type="checkbox" name="wo3" {'checked' if form.getfirst('wo3') else ''} value="Городское фэнтези">Городское фэнтези<br>
        <input type="checkbox" name="wo4" {'checked' if form.getfirst('wo4') else ''} value="Детективное фэнтези">Детективное фэнтези<br>
        <input type="checkbox" name="wo5" {'checked' if form.getfirst('wo5') else ''} value="Книги про вампиров">Книги про вампиров<br>
        <input type="checkbox" name="wo6" {'checked' if form.getfirst('wo6') else ''} value="Книги про волшебников">Книги про волшебников<br>
        <input type="checkbox" name="wo7" {'checked' if form.getfirst('wo7') else ''} value="Любовное фэнтези">Любовное фэнтези<br>
        <input type="checkbox" name="wo8" {'checked' if form.getfirst('wo8') else ''} value="Попаданцы">Попаданцы<br>
        <input type="checkbox" name="wo9" {'checked' if form.getfirst('wo9') else ''} value="Русское фэнтези">Русское фэнтези<br>
        <input type="checkbox" name="wo10" {'checked' if form.getfirst('wo10') else ''} value="Фэнтези про драконов">Фэнтези про драконов<br>
        <input type="checkbox" name="wo11" {'checked' if form.getfirst('wo11') else ''} value="Юмористическое фэнтези">Юмористическое фэнтези<br>
        <input type="submit">
    </form>
""")


json_res = list(filter(lambda x: x['rating']['votes'] > 50, json_res))
json_res.sort(key=lambda x: x['rating']['rating'], reverse=True)

with document(title="MyBookSearch") as doc:
    h1("Total: " + str(len(json_res)))

    with div().add(ol()):
        for i, obj in enumerate(json_res):
            li(a(f"{obj['rating']['rating']}/{obj['rating']['votes']} {obj['name']}",
                 href=f"https://mybook.ru{obj['absolute_url']}"))

print(doc.render())

