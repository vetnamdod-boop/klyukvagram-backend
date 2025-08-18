const express = require('express');
const bcrypt = require('bcryptjs');
const User = require('../models/User');
const router = express.Router();

router.post('/register', async (req, res) => {
  try {
    const { username, password } = req.body;
    console.log(`Регистрация: username=${username}`);
    if (!username || !password) {
      console.warn('Недостаточно данных для регистрации');
      return res.status(400).json({ error: 'Требуются username и password' });
    }
    const existingUser = await User.findOne({ username });
    if (existingUser) {
      console.warn(`Пользователь ${username} уже существует`);
      return res.status(400).json({ error: 'Имя пользователя занято' });
    }
    const hashedPassword = await bcrypt.hash(password, 10);
    const user = new User({ username, password: hashedPassword });
    await user.save();
    console.log(`Пользователь ${username} успешно зарегистрирован`);
    res.status(201).json({ message: 'Пользователь зарегистрирован', username });
  } catch (err) {
    console.error('Ошибка регистрации:', err.message);
    res.status(500).json({ error: 'Ошибка сервера при регистрации' });
  }
});

router.post('/login', async (req, res) => {
  try {
    const { username, password } = req.body;
    console.log(`Вход: username=${username}`);
    const user = await User.findOne({ username });
    if (!user) {
      console.warn(`Пользователь ${username} не найден`);
      return res.status(400).json({ error: 'Неверное имя пользователя или пароль' });
    }
    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) {
      console.warn(`Неверный пароль для ${username}`);
      return res.status(400).json({ error: 'Неверное имя пользователя или пароль' });
    }
    console.log(`Пользователь ${username} успешно вошёл`);
    res.status(200).json({ message: 'Вход успешен', username });
  } catch (err) {
    console.error('Ошибка входа:', err.message);
    res.status(500).json({ error: 'Ошибка сервера при входе' });
  }
});

router.get('/users', async (req, res) => {
  try {
    console.log('Запрос списка пользователей');
    const users = await User.find({}, 'username');
    console.log(`Найдено ${users.length} пользователей`);
    res.status(200).json(users.map(user => user.username));
  } catch (err) {
    console.error('Ошибка получения пользователей:', err.message);
    res.status(500).json({ error: 'Ошибка сервера при получении пользователей' });
  }
});

module.exports = router;
