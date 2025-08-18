const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const authRoutes = require('./routes/auth');
require('dotenv').config();

const app = express();
app.use(cors());
app.use(express.json());

mongoose.connect(process.env.MONGO_URI, {
  useNewUrlParser: true,
  useUnifiedTopology: true
}).then(() => console.log('MongoDB connected'))
  .catch(err => console.error('MongoDB connection error:', err));

app.use('/api/auth', authRoutes);

const Message = mongoose.model('Message', new mongoose.Schema({
  chatId: String,
  sender: String,
  content: String,
  timestamp: { type: Date, default: Date.now }
}));

const responseMessages = [
  'блюю',
  'наблювала',
  'карета горит',
  'блюю на горящую карету'
];

function generateResponse(chatId) {
  const randomIndex = Math.floor(Math.random() * (responseMessages.length + 2));
  if (randomIndex < responseMessages.length) return responseMessages[randomIndex];
  if (randomIndex === responseMessages.length) return `наблювала на ${chatId}`;
  return `${chatId} умерлаааааааааааа`;
}

app.get('/api/messages/:chatId', async (req, res) => {
  try {
    const messages = await Message.find({ chatId: req.params.chatId }).sort('timestamp');
    res.status(200).json(messages);
  } catch (err) {
    console.error('Error fetching messages:', err);
    res.status(500).json({ error: 'Server error' });
  }
});

app.post('/api/messages', async (req, res) => {
  try {
    const { chatId, sender, content } = req.body;
    if (!chatId || !sender || !content) return res.status(400).json({ error: 'Missing fields' });
    const message = new Message({ chatId, sender, content });
    await message.save();

    // Автоматический ответ
    const responseContent = generateResponse(chatId);
    const responseMessage = new Message({ chatId, sender: chatId, content: responseContent });
    await responseMessage.save();

    res.status(201).json(message);
  } catch (err) {
    console.error('Error saving message:', err);
    res.status(500).json({ error: 'Server error' });
  }
});

const PORT = process.env.PORT || 10000;
app.listen(PORT, '0.0.0.0', () => console.log(`Server running on port ${PORT}`));
