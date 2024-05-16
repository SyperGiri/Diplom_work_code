#-*-coding: utf-8 -*-
# !/usr/bin/env python
import requests
import Levenshtein
from bs4 import BeautifulSoup
from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
import os
from sqlalchemy import func

app = Flask(__name__)

# Определите путь к папке instance
instance_path = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(instance_path, 'developers.db')

# Установите путь к базе данных
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
db = SQLAlchemy(app)


class dev(db.Model):

    __tablename__ = "developers"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    place = db.Column(db.String(100))
    url = db.Column(db.String, nullable=False)

    def __repr__(self):
        return '<dev %r>' % self.id

class works(db.Model):

    __tablename__ = "works"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    brunches = db.Column(db.String(10), default=0)
    commits = db.Column(db.String(10), default=0)
    stars = db.Column(db.String(10), default=0)
    language = db.Column(db.String(100))
    description = db.Column(db.Text, default='Описание отсутствует')
    time_update = db.Column(db.String(100))
    id_dev = db.Column(db.Integer, db.ForeignKey("developers.id"))

    def __repr__(self):
        return '<works %r>' % self.id


def get_html(url):
    result = requests.get(url)
    return  result.text


def repsup(work, id):
    article = works.query.get(id)
    article.title = work.title
    article.brunches = work.brunches
    article.commits = work.commits
    article.stars = work.stars
    article.language = work.language
    article.description = work.description
    article.time_update = work.time_update

def proj_update(div, dev_id):
    for div in div:
        id = 0
        project_name = div.find('a', itemprop='name codeRepository')
        print(project_name.text)
        art = works.query.filter((works.title == project_name.text.strip()) and (works.id_dev == dev_id)).count()
        if art == 0 :
            flag = 0
        else:
            flag = 1
            art = works.query.filter((works.title == project_name.text.strip()) and (works.id_dev == dev_id))
            for row in art:
                id = row.id

        project_links = div.find('a', itemprop='name codeRepository').get('href')
        project_theme = div.find('p', itemprop='description')
        if project_theme != None:
            print('Описание: ', project_theme.text.strip())
            desc = project_theme.text.strip()
        else:
            print('Описание  отсутствует')
            desc = 'описание отсутствует'

        projects = 'https://github.com' + project_links
        umlprojects = get_html(projects)

        language_container = div.find('div', class_='f6 text-gray mt-2')
        if language_container:
            language = language_container.find('span', itemprop="programmingLanguage")
            if language:
                print('Используемый язык: ', language.text.strip())
                lang = language.text.strip()
            else:
                print('Используемый язык: информация отсутствует')
                lang = 'информация отсутствует'
        else:
            print('Не удалось найти контейнер для языка программирования')
            lang = 'информация отсутствует'

        project_starts = div.find('a', href=project_links + '/stargazers')
        if project_starts != None:
            print("Количество звёзд: ", project_starts.text.strip())
            stars = project_starts.text.strip()
        else:
            print('Количество звёзд: 0')
            stars = '0'

        time_update = div.find('relative-time', class_='no-wrap')
        print('Последнее обновление: ', time_update.text)
        update = time_update.text
        repspars(umlprojects, project_links, stars, update, lang, desc, project_name.text.strip(), dev_id, flag, id)
        print('---------------------------------------------------------------------------------------------------------------------------------------------------------------')




def new_dev(developer):
    try:
        db.session.add(developer)
        db.session.commit()
    except:
        return 'сука'


def new_work(work):
    try:
        db.session.add(work)
        db.session.commit()
    except:
        return 'сука'


def repspars(umlprojects, project_links, stars, update, lang, desc, project_name, dev_id, flag, id):
    soup = BeautifulSoup(umlprojects, 'lxml')

    commits = soup.find('li', class_='commits',)
    if commits != None:
        commits = commits.find('a').find('span')
        print('Колличество коммитов: ', commits.text.strip())
        com = commits.text.strip()
    else:
        print('Коммитов нет')
        com = 'Коммитов нет'

    branches = soup.find('a', href=project_links+'/branches')
    if branches != None:
        branches = branches.find('span')
        print ('Колличество веток: ', branches.text.strip())
        bra = branches.text.strip()
    else:
        print ('Веток нет')
        bra = 'Веток нет'
    work = works(title=project_name, brunches=bra, commits=com, description=desc, id_dev=dev_id, stars=stars, language=lang, time_update=update)
    if flag == 0:
        new_work(work)
    else:
        repsup(work,id)


def parser(repositories, url):
    soup = BeautifulSoup(repositories, 'lxml')
    name = soup.find('span', class_='p-name')
    place = soup.find('span', class_='p-label')
    print(name.text)
    print(place.text,'\n\n')
    developer = dev(name=name.text, place=place.text, url=url)
    devurl = dev.query.all()
    flag = 0
    for devurl in devurl:
     if developer.url != devurl.url:
         flag = flag
     else:
         flag = 1
         print("такая запись уже есть")
    if flag == 0:
        new_dev(developer)

    article = dev.query.filter(dev.url == url)
    for row in article:
        dev_id = row.id
    while True:
        reps_div = soup.find_all('div', class_='col-10 col-lg-9 d-inline-block')
        proj_update(reps_div, dev_id)
        next_page = soup.find('a', class_='btn btn-outline BtnGroup-item', text='Next')
        if next_page != None:
            page = next_page.get('href')
            print(page)
            page = get_html(page)
            soup = BeautifulSoup(page, 'lxml')
        else:
            break



@app.route('/')
def index ():
    return render_template("home.html")



@app.route('/url', methods=['POST'])
def doit():
    input_url = request.form['iurl']
    print(input_url)
    main(input_url)
    b = dev.query.all()
    c = works.query.all()
    print(b)
    print(c)
    return render_template('home.html', b=b, c=c)

def main(input_url):
    url = input_url
    repurl = url + '?tab=repositories'
    repositories = get_html(repurl)
    parser(repositories, url)

@app.route('/del')
def delite():
    id = 5
    a = dev.query.get_or_404(id)
    try:
        db.session.delete(a)
        db.session.commit()
    except:
        print('gg')
    w = works.query.filter(works.id_dev == id)
    for row in w:
        try:
            db.session.delete(row)
            db.session.commit()
        except:
            print('gg')

    return render_template('home.html')


@app.route('/bd')
def bd():
    b = dev.query.all()
    c = works.query.all()
    print(b)
    print(c)
    return render_template('bd.html', b=b, c=c)


@app.route('/raz')
def raz():
    b = dev.query.all()
    print(b)
    return render_template('raz.html', b=b)


@app.route('/raz/<int:id>')
def projects(id):
    a = works.query.filter(works.id_dev == id)
    return render_template('works.html', a=a)


@app.route('/poisk', methods=['POST'])
def find():
    input_word = request.form['iword']
    lev = request.form['lev']
    devs = dev.query.all()
    n = dev.query.count()
    print(n)
    a = [0] * n
    for devs in devs:
        count = 0
        projs = works.query.filter(works.id_dev == devs.id)
        for projs in projs:
            text = projs.title + " " + projs.language + " " + projs.description
            words = text.replace('-', ' ').replace("_", ' ').split(" ")
            for words in words:
                inw = input_word
                while len(inw) > len(words):
                    words= words + " "

                while len(words) > len(inw):
                    inw = inw + " "

                dif = Levenshtein.distance(inw, words)
                if dif <= int(lev):
                    count = count+1
                    print (dif)
                    print (words + '1')
                    print(inw)
                    a[projs.id_dev - 1] = count
    d = max(a)
    if d == 0 :
        return render_template('notfind.html')
    else:
        id = a.index(d) + 1
        develop = dev.query.get(id)
        print (develop, d)
        return render_template('find.html', b=develop, d=d)



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()
