from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from pymongo import MongoClient
from pymongo.errors import BulkWriteError
from datetime import datetime
import pymongo

app = Flask(__name__)
app.config.from_pyfile('config.py')
app.secret_key = 'xyz1234nbg789ty8inmcv2134'
client = MongoClient('mongodb://localhost:27017/')
db = client['user_login_system']
users_collection = db['users']
events_collection = db['events']
winner1_collection = db['winner1']
winner2_collection = db['winner2']
competition1_collection = db['competition1']
competition2_collection = db['competition2']
participants1_collection=db['participants1']
participants2_collection=db['participants2']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']

    if username == 'admin' and password == 'admin':
        session['username'] = 'admin'
        session['role'] = 'admin'
        return jsonify(success=True)
    elif username == 'admin1' and password == 'admin1':
        session['username'] = 'admin1'
        session['role'] = 'admin1'
        return jsonify(success=True)
    else:
        return jsonify(success=False, message='Invalid credentials. Please try again.')



@app.route('/competition_selection')
def competition_selection():
    return render_template('competition_selection.html')

@app.route('/competition1', methods=['GET', 'POST'])
def competition1():
    if 'role' in session and session['role'] != 'admin':
        return render_template('error.html', message="Admin is not allowed to mark attendance for Competition 2.")
    if request.method == 'POST':
        try:
            for key, value in request.form.items():
                if key.startswith('attendance_'):
                    user_id = key.split('_')[1]
                    attendance = value == 'on'  # Convert 'on' to boolean
                    # Update attendance status in the competition1_collection
                    competition1_collection.update_one(
                        {'user_id': user_id},
                        {'$set': {'attendance': attendance}},
                        upsert=True
                    )
            return redirect(url_for('competition_selection'))
        except Exception as e:
            return f"An error occurred: {str(e)}"
    else:
        try:
            # Check if data from events_collection is already copied to competition1_collection
            if competition1_collection.count_documents({}) == 0:
                # Copy all data from events_collection to competition1_collection
                events_cursor = events_collection.find({'event_name': 'Competition 1'})
                for event_data in events_cursor:
                    user_id = event_data['_id']
                    username = event_data['username']
                    competition1_collection.insert_one({'user_id': user_id, 'username': username, 'attendance': False})

            # Retrieve participants for 'Competition 1' from competition1_collection
            competition1_participants_cursor = competition1_collection.find()

            # Convert cursor to list of dictionaries
            competition1_participants = list(competition1_participants_cursor)

            # Retrieve existing attendance data
            existing_attendance_data = {doc['user_id']: doc.get('attendance', False) for doc in competition1_participants}

            return render_template('competition1.html', competition1_participants=competition1_participants, attendance_data=existing_attendance_data)
        except Exception as e:
            return f"An error occurred: {str(e)}"

@app.route('/participants1', methods=['GET', 'POST'])
def participants1():
    if 'role' in session and session['role'] != 'admin':
        return render_template('error.html', message="Admin is not allowed to enter marks for Competition 1.")
    
    if request.method == 'POST':
        user_data = {}
        for key, value in request.form.items():
            if key.startswith('round1_') or key.startswith('round2_'):
                user_id = key.split('_')[1]
                round_number = key.split('_')[0][-1]
                round_marks = int(value)
                username = 'Unknown'  # Default username
                # Fetch username from competition1_collection
                participant_info = competition1_collection.find_one({'user_id': user_id})
                if participant_info:
                    username = participant_info.get('username', 'Unknown')

                # Update participants1_collection with round marks and username
                participants1_collection.update_one(
                    {'user_id': user_id},
                    {'$set': {f'round{round_number}_marks': round_marks, 'username': username}},
                    upsert=True
                )

                # Update user_data with round marks and username
                if user_id in user_data:
                    user_data[user_id]['total_marks'] += round_marks
                    user_data[user_id]['round_count'] += 1
                else:
                    user_data[user_id] = {'username': username, 'total_marks': round_marks, 'round_count': 1}
                    
        # Calculate average marks and update winner1_collection
        for user_id, data in user_data.items():
            average_marks = data['total_marks'] / data['round_count']
            winner1_collection.update_one(
                {'user_id': user_id},
                {'$set': {'username': data['username'], 'average_marks': average_marks}},
                upsert=True
            )
            
        return redirect(url_for('competition_selection'))
    
    else:
        try:
            # Retrieve participants with attendance marked as true from competition1_collection
            participants1_users = []
            for participant in competition1_collection.find({'attendance': True}):
                user_id = participant.get('user_id')
                username = participant.get('username', 'Unknown')
                participants1_users.append({'user_id': user_id, 'username': username})
                
            return render_template('participants1.html', participants1_users=participants1_users)
        except Exception as e:
            return f"An error occurred: {str(e)}"


@app.route('/competition2', methods=['GET', 'POST'])
def competition2():
    if 'role' in session and session['role'] != 'admin1':
        return render_template('error.html', message="Admin is not allowed to mark attendance for Competition 2.")
    if request.method == 'POST':
        try:
            for key, value in request.form.items():
                if key.startswith('attendance_'):
                    user_id = key.split('_')[1]
                    attendance = value == 'on'  # Convert 'on' to boolean
                    # Update attendance status in the competition1_collection
                    competition2_collection.update_one(
                        {'user_id': user_id},
                        {'$set': {'attendance': attendance}},
                        upsert=True
                    )
            return redirect(url_for('competition_selection'))
        except Exception as e:
            return f"An error occurred: {str(e)}"
    else:
        try:
            # Check if data from events_collection is already copied to competition1_collection
            if competition2_collection.count_documents({}) == 0:
                # Copy all data from events_collection to competition1_collection
                events_cursor = events_collection.find({'event_name': 'Competition 2'})
                for event_data in events_cursor:
                    user_id = event_data['_id']
                    username = event_data['username']
                    competition2_collection.insert_one({'user_id': user_id, 'username': username, 'attendance': False})

            # Retrieve participants for 'Competition 1' from competition1_collection
            competition2_participants_cursor = competition2_collection.find()

            # Convert cursor to list of dictionaries
            competition2_participants = list(competition2_participants_cursor)

            # Retrieve existing attendance data
            existing_attendance_data = {doc['user_id']: doc.get('attendance', False) for doc in competition2_participants}

            return render_template('competition2.html', competition2_participants=competition2_participants, attendance_data=existing_attendance_data)
        except Exception as e:
            return f"An error occurred: {str(e)}"
@app.route('/participants2', methods=['GET', 'POST'])
def participants2():
    if 'role' in session and session['role'] != 'admin1':
        return render_template('error.html', message="Admin is not allowed to enter marks for Competition 1.")
    
    if request.method == 'POST':
        user_data = {}
        for key, value in request.form.items():
            if key.startswith('round1_') or key.startswith('round2_'):
                user_id = key.split('_')[1]
                round_number = key.split('_')[0][-1]
                round_marks = int(value)
                username = 'Unknown'  # Default username
                # Fetch username from competition1_collection
                participant_info = competition2_collection.find_one({'user_id': user_id})
                if participant_info:
                    username = participant_info.get('username', 'Unknown')

                # Update participants1_collection with round marks and username
                participants2_collection.update_one(
                    {'user_id': user_id},
                    {'$set': {f'round{round_number}_marks': round_marks, 'username': username}},
                    upsert=True
                )

                # Update user_data with round marks and username
                if user_id in user_data:
                    user_data[user_id]['total_marks'] += round_marks
                    user_data[user_id]['round_count'] += 1
                else:
                    user_data[user_id] = {'username': username, 'total_marks': round_marks, 'round_count': 1}
                    
        # Calculate average marks and update winner1_collection
        for user_id, data in user_data.items():
            average_marks = data['total_marks'] / data['round_count']
            winner2_collection.update_one(
                {'user_id': user_id},
                {'$set': {'username': data['username'], 'average_marks': average_marks}},
                upsert=True
            )
            
        return redirect(url_for('competition_selection'))
    
    else:
        try:
            # Retrieve participants with attendance marked as true from competition1_collection
            participants2_users = []
            for participant in competition2_collection.find({'attendance': True}):
                user_id = participant.get('user_id')
                username = participant.get('username', 'Unknown')
                participants2_users.append({'user_id': user_id, 'username': username})
                
            return render_template('participants2.html', participants2_users=participants2_users)
        except Exception as e:
            return f"An error occurred: {str(e)}"



# @app.route('/competition2', methods=['GET', 'POST'])
# def competition2():
#     # Restrict admin1 from entering marks for competition1
#     if 'role' in session and session['role'] != 'admin1':
#         return render_template('error.html', message="Admin is not allowed to mark attendance for Competition 2.")
    
#     if request.method == 'POST':
        
#         for key, value in request.form.items():
            
#             if key.startswith('attendance_'):
#                 user_id = key.split('_')[1]
#                 competition2_collection.update_one(
#                     {'user_id': user_id},
#                     {'$set': {'event_name': 'Competition 2'}},
#                     upsert=True
#                 )
#                 attendance = value
                
#                 # Update attendance status in the participants1 table
#                 participants2_collection.update_one(
#                     {'user_id': user_id},
#                     {'$set': {'attendance': attendance}},
#                     upsert=True
#                 )
#         return redirect(url_for('competition_selection'))
#     else:
#         competition2_users = events_collection.find({'event_name': 'Competition 2'})
#         return render_template('competition2.html', competition2_users=competition2_users)


# @app.route('/participants2', methods=['GET', 'POST'])
# def participants2():
#     if 'role' in session and session['role'] != 'admin1':
#         return render_template('error.html', message="Admin is not allowed to enter marks for Competition 1.")
    
#     if request.method == 'POST':
#         user_data = {}
#         for key, value in request.form.items():
#             if key.startswith('round1_') or key.startswith('round2_'):
#                 user_id = key.split('_')[1]
#                 round_number = key.split('_')[0][-1]
#                 round_marks = int(value)
#                 user_info = users_collection.find_one({'_id': user_id})
#                 username = user_info.get('username', 'Unknown')  # Fetch 'username' field
#                 participants2_collection.update_one(
#                     {'user_id': user_id},
#                     {'$set': {f'round{round_number}_marks': round_marks, 'username': username}},
#                     upsert=True
#                 )

#                 if user_id in user_data:
#                     user_data[user_id]['total_marks'] += round_marks
#                     user_data[user_id]['round_count'] += 1
#                 else:
#                     user_data[user_id] = {'username': username, 'total_marks': round_marks, 'round_count': 1}
                    
#         for user_id, data in user_data.items():
#             average_marks = data['total_marks'] / data['round_count']
#             winner2_collection.update_one(
#                 {'user_id': user_id},
#                 {'$set': {'username': data['username'], 'average_marks': average_marks}},
#                 upsert=True
#             )
            
#         return redirect(url_for('competition_selection'))
    
#     else:
#         # Retrieve participants with attendance marked as true from competition1_collection
#         participants2_users = competition2_collection.find({'attendance': True})
#         return render_template('participants2.html', participants2_users=participants2_users)
# @app.route('/participants2', methods=['GET', 'POST'])
# def participants2():
#     if 'role' in session and session['role'] != 'admin1':
#         return render_template('error.html', message="Admin is not allowed to enter marks for Competition 2.")
    
#     if request.method == 'POST':
#         user_data = {}
#         for key, value in request.form.items():
#             if key.startswith('round1_') or key.startswith('round2_'):
#                 user_id = key.split('_')[1]
#                 round_number = key.split('_')[0][-1]
#                 round_marks = int(value)
#                 user_info = users_collection.find_one({'_id': user_id})
#                 username = user_info.get('username', 'Unknown')  # Fetch 'username' field
#                 participants2_collection.update_one(
#                     {'user_id': user_id},
#                     {'$set': {f'round{round_number}_marks': round_marks, 'username': username}},
#                     upsert=True
#                 )

#                 if user_id in user_data:
#                     user_data[user_id]['total_marks'] += round_marks
#                     user_data[user_id]['round_count'] += 1
#                 else:
#                     user_data[user_id] = {'username': username, 'total_marks': round_marks, 'round_count': 1}
#             elif key.startswith('attendance_'):
#                 user_id = key.split('_')[1]
#                 attendance = value
#                 participants2_collection.update_one(
#                     {'user_id': user_id},
#                     {'$set': {'attendance': attendance}},
#                     upsert=True
#                 )
#         for user_id, data in user_data.items():
#             average_marks = data['total_marks'] / data['round_count']
#             winner2_collection.update_one(
#                 {'user_id': user_id},
#                 {'$set': {'username': data['username'], 'average_marks': average_marks}},
#                 upsert=True
#             )
#         return redirect(url_for('competition_selection'))
#     else:
#         participants2_users = participants2_collection.find({'attendance': 'on'})
#         return render_template('participants2.html', participants2_users=participants2_users)

@app.route('/winner1', methods=['GET'])
def winner1():
    # Restrict admin from viewing the winner1 page
    if 'role' in session and session['role'] != 'admin1':
        return render_template('error.html', message="Admin is not allowed to view this page.")

    winners_cursor = winner2_collection.find().sort('average_marks', pymongo.DESCENDING).limit(2)
    winners_list = list(winners_cursor)
    return render_template('winner1.html', winners=winners_list)



@app.route('/winner', methods=['GET'])
def winner():
    if 'role' in session and session['role'] != 'admin':
        return render_template('error.html', message="Admin is not allowed to view this page.")
    # Retrieve the first two winners from the winner1 collection
    winners_cursor = winner1_collection.find().sort('average_marks', pymongo.DESCENDING).limit(2)
    winners_list = list(winners_cursor)
    return render_template('winner.html', winners=winners_list)




if __name__ == '__main__':
    app.run(debug=True)
