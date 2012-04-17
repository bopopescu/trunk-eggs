_testing_db_uri = None
def get_testing_db_uri():
    global _testing_db_uri
    from manage import create_app
    if _testing_db_uri is None:
        tmp_app = create_app()
        _testing_db_uri = tmp_app.config['TESTING_DATABASE_URI']
    return _testing_db_uri


def create_mock_app():
    from manage import create_app
    import database
    app = create_app()
    app.config["TESTING"] = True
    app.config["DATABASE_URI"] = get_testing_db_uri()
    database.initialize_app(app)

    with app.test_request_context():
        database.get_session().create_all()

    def app_teardown():
        with app.test_request_context():
            database.get_session().drop_all()

    return app, app_teardown
