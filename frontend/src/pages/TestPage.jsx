export default function TestPage() {
  return (
    <div style={{ padding: '20px', fontFamily: 'Arial' }}>
      <h1 style={{ color: 'blue', fontSize: '32px' }}>✅ React يعمل بنجاح!</h1>
      <p>إذا رأيت هذه الرسالة، فإن React و Router يعملان</p>
      <div style={{ marginTop: '20px', padding: '10px', border: '2px solid green' }}>
        <h2>معلومات التطبيق:</h2>
        <ul>
          <li>Path: {window.location.pathname}</li>
          <li>Host: {window.location.host}</li>
        </ul>
      </div>
      <div style={{ marginTop: '20px' }}>
        <a href="/login" style={{ color: 'blue', textDecoration: 'underline' }}>
          اذهب إلى صفحة Login
        </a>
      </div>
    </div>
  );
}
