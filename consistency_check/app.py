import connexion





app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("consistency_check.yaml", base_path = "/consistency-check", strict_validation = True, validate_responses = True)


if __name__ == "__main__":
    app.run(port=8300, host="0.0.0.0")