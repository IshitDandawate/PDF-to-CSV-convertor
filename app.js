const express = require('express');
const fileUpload = require('express-fileupload');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
const axios = require('axios');

const app = express();
const PORT = 3000;
let uploadPath='';

app.use(express.static('public'));
app.use(express.urlencoded({ extended: true }));
app.use(express.json());
app.use(fileUpload());

app.set('view engine', 'ejs');

app.get('/', async (req, res) => {
    try {
        const factResponse = await axios.get('https://api.api-ninjas.com/v1/facts', {
            headers: { 'X-Api-Key': 'Cz/vUMzQcCRn/fbj8rcehg==krHVCtQGr0r1RYin' }
        });
        const fact = factResponse.data[0]?.fact || "Did you know?";
        res.render('index', { fact });
    } catch (error) {
        console.error(error);
        res.render('index', { fact: "Did you know?" });
    }
});

app.post('/upload', (req, res) => {
    if (!req.files || !req.files.pdfFile || !req.body.query) {
        return res.status(400).send('No file or query provided.');
    }

    const pdfFile = req.files.pdfFile;
    const query = req.body.query;
    uploadPath = path.join(__dirname, 'uploads', pdfFile.name);

    pdfFile.mv(uploadPath, (err) => {
        if (err) {
            return res.status(500).send(err);
        }

        const pythonProcess = spawn('python', ['script.py', uploadPath, query]);

        let result = '';
        pythonProcess.stdout.on('data', (data) => {
            result += data.toString();
        });

        pythonProcess.stderr.on('data', (data) => {
            console.error(`stderr: ${data}`);
        });

        pythonProcess.on('close', (code) => {
            if (code !== 0) {
                return res.status(500).send('Error during PDF conversion and query.');
            }

            const [answerLine, csvLine] = result.trim().split('\n').slice(-2);
            const answer = answerLine.split(': ')[1];
            const csvPath = csvLine.split(': ')[1];

            res.json({ answer, csvPath });
        });
    });
});

app.get('/download', (req, res) => {
    // const csvPath = decodeURIComponent(req.query.csvPath);
    // console.log(">>>"+csvPath);
    const csvPath=uploadPath.replace('.pdf','.csv')
    console.log(csvPath);

    if (!csvPath || !fs.existsSync(csvPath)) {
        return res.status(404).send('CSV file not found.');
    }

    res.download(csvPath, (err) => {
        if (err) {
            console.error(err);
            res.status(500).send('Error downloading the file.');
        }
    });
});

app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});
