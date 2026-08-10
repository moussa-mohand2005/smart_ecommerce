import mysql from "mysql2/promise";
import { config } from "dotenv";
import path from "node:path";

if (!process.env.DB_HOST) {
  config({ path: path.resolve(process.cwd(), "..", ".env") });
}

const globalForDb = globalThis as unknown as { shoePool?: mysql.Pool };
const dbHost = process.env.DB_HOST ?? "localhost";
const connectionTarget = dbHost.startsWith("/cloudsql/")
  ? { socketPath: dbHost }
  : { host: dbHost, port: Number(process.env.DB_PORT ?? 3306) };

export const pool = globalForDb.shoePool ?? mysql.createPool({
  ...connectionTarget,
  user: process.env.DB_USER ?? "root",
  password: process.env.DB_PASS ?? "",
  database: process.env.DB_NAME ?? "smart_ecommerce",
  waitForConnections: true,
  connectionLimit: 10,
  maxIdle: 5,
  idleTimeout: 60_000,
  decimalNumbers: true,
  charset: "utf8mb4",
});

if (process.env.NODE_ENV !== "production") globalForDb.shoePool = pool;
