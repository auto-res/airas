---
sidebar_position: 1
---

# ページの作成

**独立したページ**を作成するには、`src/pages`に**MarkdownまたはReact**ファイルを追加します：

- `src/pages/index.js` → `localhost:3000/`
- `src/pages/foo.md` → `localhost:3000/foo`
- `src/pages/foo/bar.js` → `localhost:3000/foo/bar`

## 最初のReactページを作成する

`src/pages/my-react-page.js`にファイルを作成します：

```jsx title="src/pages/my-react-page.js"
import React from 'react';
import Layout from '@theme/Layout';

export default function MyReactPage() {
  return (
    <Layout>
      <h1>私のReactページ</h1>
      <p>これはReactページです</p>
    </Layout>
  );
}
```

新しいページが[http://localhost:3000/my-react-page](http://localhost:3000/my-react-page)で利用可能になりました。

## 最初のMarkdownページを作成する

`src/pages/my-markdown-page.md`にファイルを作成します：

```mdx title="src/pages/my-markdown-page.md"
# 私のMarkdownページ

これはMarkdownページです
```

新しいページが[http://localhost:3000/my-markdown-page](http://localhost:3000/my-markdown-page)で利用可能になりました。
