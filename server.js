const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const authRoutes = require('./routes/auth');
require('dotenv').config();

const app = express();
app.use(cors({ origin: '*' }));
app.use(express.json({ limit: '10mb' }));

// Подключение к MongoDB
mongoose.connect(process.env.MONGO_URI, {
  useNewUrlParser: true,
  useUnifiedTopology: true,
  serverSelectionTimeoutMS: 5000
}).then(() => console.log('MongoDB успешно подключен'))
  .catch(err => console.error('Ошибка подключения MongoDB:', err.message));

// Модель сообщений
const MessageSchema = new mongoose.Schema({
  chatId: { type: String, required: true },
  sender: { type: String, required: true },
  content: { type: String, required: true },
  timestamp: { type: Date, default: Date.now }
});
const Message = mongoose.model('Message', MessageSchema);

// Роуты авторизации
app.use('/api/auth', authRoutes);

// Получение сообщений
app.get('/api/messages/:chatId', async (req, res) => {
  try {
    console.log(`Запрос сообщений для chatId: ${req.params.chatId}`);
    const messages = await Message.find({ chatId: req.params.chatId })
      .sort({ timestamp: 1 })
      .limit(100);
    console.log(`Найдено ${messages.length} сообщений`);
    res.status(200).json(messages);
  } catch (err) {
    console.error('Ошибка получения сообщений:', err.message);
    res.status(500).json({ error: 'Ошибка сервера при получении сообщений' });
  }
});

// Отправка сообщения
app.post('/api/messages', async (req, res) => {
  try {
    const { chatId, sender, content } = req.body;
    console.log(`Получено сообщение: chatId=${chatId}, sender=${sender}, content=${content}`);
    if (!chatId || !sender || !content) {
      console.warn('Недостаточно данных в запросе');
      return res.status(400).json({ error: 'Требуются chatId, sender и content' });
    }
    const message = new Message({ chatId, sender, content });
    await message.save();
    console.log('Сообщение сохранено:', message);
    res.status(201).json(message);
  } catch (err) {
    console.error('Ошибка сохранения сообщения:', err.message);
    res.status(500).json({ error: 'Ошибка сервера при сохранении сообщения' });
  }
});

// Тестовый эндпоинт
app.get('/api/health', (req, res) => {
  console.log('Проверка состояния сервера');
  res.status(200).json({ status: 'Сервер работает', timestamp: new Date() });
});

const PORT = process.env.PORT || 10000;
app.listen(PORT, '0.0.0.0', () => console.log(`Сервер запущен на порту ${PORT}`));
