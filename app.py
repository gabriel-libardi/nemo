from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)


class User(UserMixin):
    def __init__(self, id):
        self.id = id


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


app.jinja_env.globals['title'] = 'NEMO'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.secret_key = 'sua_chave_secreta_aqui'
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    tags = db.Column(db.Text, nullable=True)
    content = db.Column(db.Text, nullable=False)
    desc = db.Column(db.String(200), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    image_path = db.Column(db.String(255))

    def __repr__(self):
        return f'<Post {self.title}>'

# Rota de login


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Verifique se o usuário e a senha estão corretos (simulação simples)
        if username == 'admin' and password == 'password':
            user = User(1)  # Crie um objeto de usuário
            login_user(user)  # Faça login no usuário
            # Redirecione para a página protegida
            return redirect(url_for('index'))
    return render_template('login.html')


# Rota de logout
@app.route('/logout')
@login_required
def logout():
    logout_user()  # Faça logout do usuário
    return redirect(url_for('index'))  # Redirecione para a página de login


@app.route('/')
def index():
    posts = Post.query.order_by(Post.id.desc()).all()
    return render_template('index.html', logado=current_user.is_authenticated, post_list=posts, len_post_list=len(posts))


@app.route('/about')
def about():
    return render_template('about.html', logado=current_user.is_authenticated)


@app.route('/faq')
def faq():
    return render_template('faq.html', logado=current_user.is_authenticated)


@app.route('/months-problems')
def months_problems():
    posts = Post.query.order_by(Post.id.desc()).all()
    return render_template('months-problems.html', logado=current_user.is_authenticated, post_list=posts, len_post_list=len(posts))


@app.route('/news')
def news():
    posts = Post.query.order_by(Post.id.desc()).all()
    return render_template('news.html', logado=current_user.is_authenticated, post_list=posts, len_post_list=len(posts))


@app.route('/contact')
def contact():
    return render_template('contact.html', logado=current_user.is_authenticated)


@app.route('/materials')
def materials():
    return render_template('materials.html', logado=current_user.is_authenticated)


@app.route('/create-post', methods=['GET'])
@login_required
def create_post_get():
    return render_template('create-post.html', logado=current_user.is_authenticated)


@app.route('/create-post', methods=['POST'])
@login_required
def create_post_post():
    # Obter os dados do formulário
    title = request.form.get('post-title')
    desc = request.form.get('post-desc')
    content = request.form.get('post-content')  # .replace('\r\n', '\n')
    tags = request.form.get('post-tags')
    image = request.files['image'] if 'image' in request.files else None

    # Processar as tags
    as_tags = tags.split('\r\n')
    as_tags = [a_tag for a_tag in as_tags if a_tag != '']
    if len(as_tags) == 0:
        as_tags.append('sem')
    as_tags = '|'.join(as_tags)

    # Salvar a imagem no servidor, se existir
    if image:
        filename = secure_filename(image.filename)
        base_filename, file_extension = os.path.splitext(filename)
        counter = 0
        while os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
            counter += 1
            filename = f"{base_filename}_{counter}{file_extension}"
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)
    else:
        image_path = None

    # Criar o novo post
    new_post = Post(title=title, content=content,
                    tags=as_tags, image_path=image_path, desc=desc)
    db.session.add(new_post)
    db.session.commit()

    return jsonify({'success': True, 'post_id': new_post.id})


@app.route('/edit-post/<post_id>', methods=['GET'])
@login_required
def edit_post_get(post_id):
    post = db.session.get(Post, post_id)
    post_data = {'pid': post.id, 'ptitle': post.title,
                 'pcontent': post.content, 'ptags': post.tags, 'pimg_path': post.image_path,
                 'pdate': post.date, 'pdesc': post.desc}
    return render_template('edit-post.html', logado=current_user.is_authenticated, **post_data)


@app.route('/edit-post/<post_id>', methods=['POST'])
@login_required
def edit_post_post(post_id):
    # Obter os dados do formulário
    post = db.session.get(Post, post_id)
    title = request.form.get('post-title')
    desc = request.form.get('post-desc')
    content = request.form.get('post-content')  # .replace('\r\n', '\n')
    tags = request.form.get('post-tags')
    image = request.files['image'] if 'image' in request.files else None

    # Processar as tags
    as_tags = tags.split('\n')
    as_tags = [a_tag for a_tag in as_tags if a_tag != '']
    if len(as_tags) == 0:
        as_tags.append('sem')
    as_tags = '|'.join(as_tags)

    post.title = title
    post.desc = desc
    post.content = content
    post.tags = as_tags

    # Salvar a imagem no servidor, se existir
    if image:
        filename = secure_filename(image.filename)
        base_filename, file_extension = os.path.splitext(filename)
        counter = 0
        while os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
            counter += 1
            filename = f"{base_filename}_{counter}{file_extension}"
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)
        if post.image_path is not None:
            os.remove(post.image_path)
        post.image_path = image_path
    else:
        image_path = None

    # Criar o novo post
    db.session.commit()

    return jsonify({'success': True, 'post_id': post_id})


@app.route('/view-posts')
@login_required
def view_posts():
    posts = Post.query.all()
    output = []
    for post in posts:
        post_data = {'id': post.id, 'title': post.title,
                     'content': post.content, 'tags': post.tags,
                     'desc': post.desc}
        output.append(post_data)
    return jsonify({'posts': output})


@app.route('/post/<int:post_id>', methods=['GET'])
def view_post(post_id):
    post = db.session.get(Post, post_id)
    post_data = {'pid': post.id, 'ptitle': post.title,
                 'pcontent': post.content, 'ptags': post.tags, 'pimg_path': post.image_path,
                 'pdate': post.date, 'pdesc': post.desc}
    return render_template('view-post.html', logado=current_user.is_authenticated, **post_data)


@app.route('/delete-post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = db.session.get(Post, post_id)
    confirmation = request.form.get('confirmation')

    if confirmation != 'deleta':
        return redirect(url_for('view_post', post_id=post_id))

    image_path = post.image_path
    if image_path is not None:
        os.remove(image_path)

    # Deletar o post
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('index'))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host='localhost', port=5000)
