import express from "express";
import bodyParser from "body-parser";
import nodemailer from "nodemailer";
import { exec } from "child_process";
import path from "path";
import { fileURLToPath } from "url";
import cors from "cors";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: false }));
app.use(bodyParser.json());

const transporter = nodemailer.createTransport({
  service: "gmail",
  auth: {
    user: "mypersonaluser333@gmail.com",
    pass: "ynme rxju krad ibnz",
  },
});

app.post("/", (req, res) => {
  const { key, email, numImages } = req.body;
  console.log(`Received key: ${key}, email: ${email}, ${numImages}`);

  const scriptPath = path.join(__dirname, "python.py");
  const command = `python ${scriptPath} ${key} ${numImages}`;

  console.log(`Executing command: ${command}`);
exec(command, (error, stdout, stderr) => {
  if (error) {
    console.log(`Execution Error: ${error.message}`);
    return res.status(500).send({ Error: error.message });
  }

  if (stderr) {
    console.log(`Stderr (non-fatal): ${stderr}`);
  }

  let result;
  try {
    result = JSON.parse(stdout.trim()); 
  } catch (parseError) {
    console.log("Raw stdout:", stdout);
    console.log(`Parse Error: ${parseError.message}`);
    return res.status(500).send({ Error: "Failed to parse Python script output" });
  }

  const { zip_path: zipPath, message, error: pyError } = result;

  if (pyError) {
    return res.status(500).send({ Error: pyError });
  }

  console.log(`Zip file created at: ${zipPath}`);

  const mailOptions = {
    from: "mypersonaluser333@gmail.com", 
    to: email,
    subject: `Images for keyword: ${key}`,
    html: "<div>PLEASE REFER TO ATTACHED ZIP FILE</div>",
    attachments: [
      {
        path: zipPath,
      },
    ],
  };

  transporter.sendMail(mailOptions, (error, info) => {
    if (error) {
      console.log(`SendMail Error: ${error.message}`);
      return res.status(500).send({ Error: error.message });
    }
    console.log("Message sent: %s", info.messageId);
    res.send({ message: message || "Images sent successfully" });
  });
});
});
app.listen(5000, () => {
  console.log("Server is running on port 5000");
});
