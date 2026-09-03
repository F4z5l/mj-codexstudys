require('dotenv').config();
const app = require('./app');
const http = require('http');
const { initSocket } = require('./socket');

const server = http.createServer(app);
initSocket(server);

server.listen(process.env.PORT || 10000, () => {
  console.log('Server running');
});
