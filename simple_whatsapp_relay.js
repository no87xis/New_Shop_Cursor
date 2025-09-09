const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(helmet());
app.use(cors());
app.use(morgan('combined'));
app.use(express.json());

// Mock WhatsApp status
let isReady = false;
let qrCode = null;

// Simulate WhatsApp initialization
setTimeout(() => {
    console.log('WhatsApp Relay started (Mock Mode)');
    isReady = true;
    qrCode = null;
}, 5000);

// Routes
app.get('/health', (req, res) => {
    res.json({
        status: 'ok',
        whatsapp_ready: isReady,
        qr_available: !!qrCode,
        mode: 'mock',
        timestamp: new Date().toISOString()
    });
});

app.get('/qr', (req, res) => {
    if (qrCode) {
        res.json({ qr: qrCode });
    } else if (isReady) {
        res.json({ message: 'WhatsApp is connected (Mock Mode)' });
    } else {
        res.status(404).json({ error: 'QR code not available' });
    }
});

app.post('/send', async (req, res) => {
    try {
        const { phone, message } = req.body;
        
        if (!phone || !message) {
            return res.status(400).json({ 
                error: 'Phone and message are required' 
            });
        }

        // Mock message sending
        console.log(`Mock sending message to ${phone}: ${message}`);
        
        res.json({
            success: true,
            messageId: 'mock_' + Date.now(),
            phone: phone,
            message: message,
            mode: 'mock',
            timestamp: new Date().toISOString()
        });

    } catch (error) {
        console.error('Error sending message:', error);
        res.status(500).json({ 
            error: 'Failed to send message',
            details: error.message
        });
    }
});

app.get('/status', (req, res) => {
    res.json({
        ready: isReady,
        qr_available: !!qrCode,
        mode: 'mock',
        client_state: 'mock_initialized'
    });
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
    console.log(`WhatsApp Relay server running on port ${PORT} (Mock Mode)`);
});

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('Shutting down WhatsApp Relay...');
    process.exit(0);
});