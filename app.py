from flask import Flask, render_template, request, redirect
import calendar
from datetime import datetime

app = Flask(__name__)

goals = []

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        title = request.form.get('title')

        # 🔥 값 없으면 무시 (에러 방지)
        if not title:
            return redirect('/')

        goals.append({'title': title, 'plans': []})
        return redirect('/goals')
    
    return render_template('index.html')


@app.route('/goals')
def goals_page():
    return render_template('goals.html', goals=goals)


@app.route('/progress/<int:goal_id>')
def progress(goal_id):
    if goal_id >= len(goals):
        return redirect('/goals')

    goal = goals[goal_id]

    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)

    # 🔥 월 범위 자동 보정
    if month < 1:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1

    cal = calendar.Calendar(firstweekday=6)
    calendar_data = cal.monthdayscalendar(year, month)

    done = 0
    total = len(goal['plans'])

    for plan in goal['plans']:
        if plan['type'] in ['count', 'time']:
            if plan.get('current', 0) >= plan.get('target', 0):
                done += 1

        elif plan['type'] == 'number':
            if plan.get('direction') == 'up':
                if plan.get('current', 0) >= plan.get('target', 0):
                    done += 1
            else:
                if plan.get('current', 0) <= plan.get('target', 0):
                    done += 1

        elif plan['type'] == 'check':
            if plan.get('done'):
                done += 1

        elif plan['type'] == 'calendar':
            if len(plan.get('checked_dates', [])) > 0:
                done += 1

    percent = int((done / total) * 100) if total > 0 else 0

    return render_template('progress.html',
                            goal=goal,
                            goal_id=goal_id,
                            percent=percent,
                            calendar_data=calendar_data,
                            year=year,
                            month=month)


@app.route('/add_plan/<int:goal_id>', methods=['POST'])
def add_plan(goal_id):
    if goal_id >= len(goals):
        return redirect('/goals')

    title = request.form.get('title')
    plan_type = request.form.get('type')

    # 🔥 값 없으면 무시
    if not title or not plan_type:
        return redirect(f'/progress/{goal_id}')

    plan = {
        'title': title,
        'type': plan_type,
        'current': 0
    }

    if plan_type in ['count', 'time']:
        target = request.form.get('target')
        plan['target'] = int(target) if target else 0

    elif plan_type == 'number':
        start = request.form.get('start')
        target = request.form.get('target')
        direction = request.form.get('direction')

        plan['start'] = int(start) if start else 0
        plan['target'] = int(target) if target else 0
        plan['current'] = plan['start']
        plan['direction'] = direction if direction else 'up'

    elif plan_type == 'check':
        plan['done'] = False

    elif plan_type == 'calendar':
        plan['checked_dates'] = []

    goals[goal_id]['plans'].append(plan)
    return redirect(f'/progress/{goal_id}')


@app.route('/update/<int:goal_id>/<int:plan_id>', methods=['POST'])
def update(goal_id, plan_id):
    if goal_id >= len(goals):
        return redirect('/goals')

    if plan_id >= len(goals[goal_id]['plans']):
        return redirect(f'/progress/{goal_id}')

    plan = goals[goal_id]['plans'][plan_id]
    value = request.form.get('value')

    if value:
        try:
            plan['current'] = int(value)
        except:
            pass  # 🔥 숫자 아니면 무시

    return redirect(f'/progress/{goal_id}')


@app.route('/check/<int:goal_id>/<int:plan_id>')
def check(goal_id, plan_id):
    if goal_id >= len(goals):
        return redirect('/goals')

    if plan_id >= len(goals[goal_id]['plans']):
        return redirect(f'/progress/{goal_id}')

    plan = goals[goal_id]['plans'][plan_id]
    plan['done'] = not plan.get('done', False)

    return redirect(f'/progress/{goal_id}')


@app.route('/calendar/<int:goal_id>/<int:plan_id>/<date>')
def calendar_check(goal_id, plan_id, date):
    if goal_id >= len(goals):
        return redirect('/goals')

    if plan_id >= len(goals[goal_id]['plans']):
        return redirect(f'/progress/{goal_id}')

    plan = goals[goal_id]['plans'][plan_id]

    if 'checked_dates' not in plan:
        plan['checked_dates'] = []

    if date in plan['checked_dates']:
        plan['checked_dates'].remove(date)
    else:
        plan['checked_dates'].append(date)

    return redirect(request.referrer or f'/progress/{goal_id}')


if __name__ == '__main__':
    app.run(debug=True)