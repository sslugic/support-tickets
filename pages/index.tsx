import React from 'react';
import TaskTicketList from '../components/TaskTicketList';

const IndexPage = ({ tasks }) => {
  return (
    <div>
      <h1>Task Tickets Dashboard</h1>
      <TaskTicketList tasks={tasks} />
    </div>
  );
};

export default IndexPage;