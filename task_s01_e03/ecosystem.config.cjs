module.exports = {
  apps: [
    {
      name: "task_s01_e03",
      script: "./server.js",
      cwd: "/home/a/agent16805/task_s01_e03",
      env: {
        PORT: 31341,
        AG3NTS_API_KEY: process.env.AG3NTS_API_KEY,
        GEMINI_API_KEY: process.env.GEMINI_API_KEY,
        GEMINI_MODEL: process.env.GEMINI_MODEL || "gemini-2.5-flash"
      }
    }
  ]
};
