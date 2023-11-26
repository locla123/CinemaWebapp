import math
from flask import render_template, request, redirect, url_for, flash, jsonify, session
from app import app, dao, login, recaptcha
from app.encode import blowfish
from flask_login import login_user, logout_user
import cloudinary.uploader


@app.route('/')
def index():
    tag_id = request.args.get('tag_id')
    genre_id = request.args.get('genre_id')
    page = int(request.args.get('page', 1))

    movies = dao.load_movies(tag_id=tag_id, genre_id=genre_id, page=page)
    page_size = math.ceil(dao.count_movie() / app.config['PAGE_SIZE'])

    return render_template('index.html',
                           movies=movies,
                           page_size=page_size)


@app.route('/user-register', methods=['POST', 'GET'])
def user_register():
    err_msg = ''
    captcha_err_msg = ''
    if not recaptcha.verify():
        captcha_err_msg = 'Please make sure you are not a robot!'
        return render_template('register.html', captcha_err_msg=captcha_err_msg)
    else:
        print('here')

        try:
            if request.method.__eq__('POST'):
                username = request.form.get('username')
                email = request.form.get('email')
                if username and email:
                    if dao.check_user_existence(email=email, username=username):
                        password = request.form.get('password')
                        confirm = request.form.get('confirm')
                        if password.strip().__eq__(confirm.strip()):  # user valid
                            full_name = request.form.get('fullName')
                            avatar = request.files.get('avatar')

                            avatar_path = None
                            if avatar:
                                res = cloudinary.uploader.upload(avatar)
                                avatar_path = res['secure_url']

                            dao.add_user(full_name=full_name,
                                         email=email,
                                         username=username,
                                         password=password,
                                         avatar_path=avatar_path,
                                         key=blowfish.generate_key())
                            return redirect(url_for('index'))
                        else:
                            err_msg = 'Confirmed password does not match!'
                            render_template('register.html', err_msg=err_msg)
                    else:
                        err_msg = 'Username or email has already been used!'
                        render_template('register.html', err_msg=err_msg)
        except Exception as ex:
            err_msg = str(ex)
            render_template('register.html', err_msg=err_msg)

    return render_template('register.html', err_msg=err_msg)


@app.route('/user-login', methods=['POST', 'GET'])
def user_login():
    err_msg = ''
    captcha_err_msg = ''

    if not recaptcha.verify():
        captcha_err_msg = 'Please make sure you are not a robot!'

        return render_template('login.html', captcha_err_msg=captcha_err_msg)
    else:
        try:
            if request.method.__eq__('POST'):
                username = request.form.get('username')
                password = request.form.get('password')
                user = dao.check_user_valid(username=username, password=password)
                if user:
                    login_user(user=user)
                    return redirect(url_for('index'))
                else:
                    err_msg = 'Username or password is incorrect!'
                    return render_template('login.html', err_msg=err_msg)
        except Exception as ex:
            err_msg = str(ex)
            return render_template('login.html', err_msg=err_msg)

        # return render_template('login.html')

    return render_template('login.html')

    # else:
    #     print('haha')
    #     flash('Error ReCaptcha')
    #     return redirect(url_for('user_login'))


@app.route('/user-logout')
def user_logout():
    logout_user()
    return redirect(url_for('index'))


@app.context_processor
def common_response():
    return {
        "genres": dao.load_genres(),
        "tags": dao.load_tags()
    }


@login.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id=user_id)


@app.route('/ticket-booking')
def book_ticket():
    movie_id = request.args.get('movie_id')
    movie = dao.get_movie_by_id(movie_id=movie_id)
    return render_template('booking.html', movie=movie)


@app.route('/movies/')
def detail():
    movie_id = request.args.get('movie_id')
    movie = dao.get_movie_by_id(movie_id=movie_id)

    return render_template('detail.html', movie=movie)


if __name__ == '__main__':
    app.run(debug=True)
