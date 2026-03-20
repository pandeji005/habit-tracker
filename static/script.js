console.log("JS loaded");

// Load habits on page load
window.onload = loadHabits;

// =========================
// ADD HABIT
// =========================
async function addHabit() {
    const input = document.getElementById("habitInput");
    const habitName = input.value;

    if (!habitName) {
        alert("Please enter a habit");
        return;
    }

    try {
        const response = await fetch("/add_habit", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            credentials: "include",   // 🔥 IMPORTANT
            body: JSON.stringify({
                name: habitName
            })
        });

        if (response.status === 401) {
            window.location.href = "/";
            return;
        }

        const data = await response.json();

        input.value = "";
        loadHabits();

    } catch (error) {
        console.error(error);
        alert("Error adding habit");
    }
}

// LOAD HABITS
// =========================
async function loadHabits() {
    try {
        const response = await fetch("/get_habits", {
            credentials: "include"   // 🔥 IMPORTANT
        });

        if (response.status === 401) {
            window.location.href = "/";
            return;
        }

        const habits = await response.json();

        const habitList = document.getElementById("habitList");
        habitList.innerHTML = "";

        for (let habit of habits) {

            const streakRes = await fetch(`/streak/${habit.id}`);
            const streakData = await streakRes.json();

            const card = document.createElement("div");
            card.className = "habit-card";

            card.innerHTML = `
                <h3>${habit.name}</h3>
                <p>🔥 Streak: ${streakData.streak}</p>
                <button onclick="completeHabit(${habit.id})">Mark Done</button>
            `;

            habitList.appendChild(card);
        }

    } catch (error) {
        console.error(error);
    }
}


// COMPLETE HABIT
// =========================
async function completeHabit(habitId) {
    const response = await fetch("/complete_habit", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        credentials: "include",   // 🔥 IMPORTANT
        body: JSON.stringify({
            habit_id: habitId
        })
    });

    const data = await response.json();

    alert(data.message);
    loadHabits();
}


// MOOD SYSTEM
// =========================
async function setMood(mood) {

    document.querySelectorAll(".mood-section button")
        .forEach(btn => btn.classList.remove("active"));

    event.target.classList.add("active");

    const response = await fetch("/add_mood", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        credentials: "include",   // 🔥 IMPORTANT
        body: JSON.stringify({
            mood: mood
        })
    });

    const data = await response.json();

    alert("Mood saved: " + mood);
}


// LOGOUT
// =========================
async function logout() {
    await fetch("/logout", {
        credentials: "include"
    });

    window.location.href = "/";
}