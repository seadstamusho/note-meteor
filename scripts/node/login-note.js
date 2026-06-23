#!/usr/bin/env node
/**
 * note.com ログインスクリプト
 * ブラウザを開いて手動ログイン後、セッション状態を保存する
 */
import { chromium } from 'playwright';
import { resolve } from 'path';
import { existsSync } from 'fs';

const STATE_PATH = process.env.NOTE_POST_MCP_STATE_PATH
  || resolve(process.env.HOME || process.env.USERPROFILE || '.', '.note-state.json');

console.log('=== note.com ログインツール ===');
console.log(`保存先: ${STATE_PATH}`);
console.log('');
console.log('ブラウザが開きます。note.com にログインしてください。');
console.log('ログイン完了後、このターミナルに戻って Enter を押してください。');
console.log('');

const browser = await chromium.launch({ headless: false });
const context = await browser.newContext();

// 既存の状態があれば復元
if (existsSync(STATE_PATH)) {
  console.log('既存のセッション状態を読み込み中...');
  try {
    const existingContext = await browser.newContext({ storageState: STATE_PATH });
    const page = await existingContext.newPage();
    await page.goto('https://note.com/');
    await page.waitForTimeout(3000);
    // ログイン済みか確認
    const isLoggedIn = await page.evaluate(() => {
      return document.querySelector('[data-testid="user-menu"]') !== null
        || document.querySelector('.o-navBarUser') !== null
        || document.querySelector('a[href="/mypage"]') !== null;
    });
    if (isLoggedIn) {
      console.log('既存セッションは有効です。更新して保存します。');
      await existingContext.storageState({ path: STATE_PATH });
      await existingContext.close();
      await browser.close();
      console.log(`\nセッション保存完了: ${STATE_PATH}`);
      process.exit(0);
    }
    await existingContext.close();
    console.log('既存セッションは期限切れです。再ログインしてください。');
  } catch {
    console.log('既存セッションの読み込みに失敗。新規ログインしてください。');
  }
}

const page = await context.newPage();
await page.goto('https://note.com/login');

console.log('ブラウザでログインしてください...');

// ユーザーの入力を待つ
process.stdin.setRawMode?.(false);
process.stdin.resume();
process.stdout.write('ログイン完了後、Enter を押してください > ');

await new Promise((resolve) => {
  process.stdin.once('data', () => resolve());
});

// セッション状態を保存
await context.storageState({ path: STATE_PATH });
console.log(`\nセッション保存完了: ${STATE_PATH}`);

await browser.close();
process.exit(0);
