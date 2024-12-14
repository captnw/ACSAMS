# ACSAMS
Another Cloud Service Access Management System. This is a school project. FASTAPI.

# Authors
William Nguyen, Randell Lapid, and Fabrizio Mejia

# Dependencies
1. Python
2. MongoDB

# To run app
1. Create python virtual environment
2. Install packages from requirements.txt
3. Create new mongodb connection with URI (see config.ini file in root; MONGODB_URL value)
4. Create new mongodb database with name (see config.ini file in root; MONGODB_DATABASE value)
5. Create the following collections in database:
   - 'users'
   - 'permissions'
   - 'plans'
6. Go to sample and import the .json file into the same collection above
7. Run `uvicorn app:app --reload`

Note: credentials are in sample/ACAMS.user.json, they are plain-text because this is a simple project. (you can hash it yourself if you want)

# To see API docs
1. Navigate to `http://127.0.0.1:8000/docs` while app is running