import { Task } from '../models/task';

function TaskTicketList({ tasks }: { tasks: Task[] }) {
    return (
        <div>
            <h2>Task Tickets</h2>
            <ul>
                {tasks.map(task => (
                    <li key={task.id}>
                        <strong>{task.id}</strong>: {task.title}
                    </li>
                ))}
            </ul>
        </div>
    );
}

export default TaskTicketList;