// 할일 목록을 저장할 배열
let tasks = JSON.parse(localStorage.getItem('tasks')) || [];

// 페이지 로드 시 저장된 할일 목록 표시
window.onload = function() {
    displayTasks();
}

// 할일 추가 함수
function addTask() {
    const taskInput = document.getElementById('taskInput');
    const taskText = taskInput.value.trim();
    
    if (taskText !== '') {
        const task = {
            id: Date.now(),
            text: taskText,
            completed: false
        };
        
        tasks.push(task);
        saveTasks();
        displayTasks();
        taskInput.value = '';
    }
}

// 할일 표시 함수
function displayTasks() {
    const taskList = document.getElementById('taskList');
    taskList.innerHTML = '';
    
    tasks.forEach(task => {
        const li = document.createElement('li');
        li.className = `group flex items-center justify-between p-3 ${task.completed ? 'bg-gray-100' : 'bg-white'} 
                       border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-all duration-200`;
        
        li.innerHTML = `
            <div class="flex items-center gap-3">
                <button onclick="toggleTask(${task.id})" 
                        class="w-6 h-6 flex items-center justify-center rounded-full 
                        ${task.completed ? 'bg-green-500 text-white' : 'border-2 border-gray-300 text-transparent'} 
                        hover:border-green-500 transition-colors duration-200">
                    <i class="fas fa-check text-sm ${task.completed ? '' : 'opacity-0'}"></i>
                </button>
                <span class="${task.completed ? 'line-through text-gray-500' : 'text-gray-700'} font-medium">
                    ${task.text}
                </span>
            </div>
            <button onclick="deleteTask(${task.id})" 
                    class="text-gray-400 hover:text-red-500 focus:outline-none transition-colors duration-200">
                <i class="fas fa-trash-alt"></i>
            </button>
        `;
        
        taskList.appendChild(li);
    });
}

// 할일 완료/미완료 토글 함수
function toggleTask(id) {
    const task = tasks.find(t => t.id === id);
    if (task) {
        task.completed = !task.completed;
        saveTasks();
        displayTasks();
    }
}

// 할일 삭제 함수
function deleteTask(id) {
    tasks = tasks.filter(task => task.id !== id);
    saveTasks();
    displayTasks();
}

// 로컬 스토리지에 할일 목록 저장
function saveTasks() {
    localStorage.setItem('tasks', JSON.stringify(tasks));
}

// Enter 키로 할일 추가
document.getElementById('taskInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        addTask();
    }
});
