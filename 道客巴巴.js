/*
代码片段实现对道客巴巴的资源爬取，道客巴巴资源采用canva来进行存储，我们使用toBlob方法画布上的内容导出为图片文件（如 PNG 或 JPEG 格式），并进行保存或上传操作。
使用方式：
1.将i变量遍历次数修改为资源的总页数
2.在开发者工具中新建js代码片段，执行下面修改后的代码即可实现下载(Sources->Snippets)
3.你可以自定义下载文件名等参数来满足你的需求
*/

for (let i = 1; i <= 19; i++) {
  //i为总页数
  const canvas = document.getElementById(`page_${i}`); //通过id获取canvas标签

  // 使用模板字符串生成文件名
  canvas.toBlob(
    //使用toBlob方法画布上的内容导出为图片文件（如 PNG 或 JPEG 格式），并进行保存或上传操作。
    (blob) => {
      (function (index) {
        // 使用 IIFE（立即执行函数表达式）封存当前 i 值
        const downloadLink = document.createElement("a");
        downloadLink.href = URL.createObjectURL(blob); // 将 Blob 对象转换为 URL
        downloadLink.download = `page${index}.png`; // 设置下载文件名
        document.body.appendChild(downloadLink); // 添加到 DOM
        downloadLink.click(); // 触发下载
        document.body.removeChild(downloadLink); // 移除 DOM
      })(i);
    },
    "image/png",
    1
  );
}

/*
以下是关于代码的详细说明解释：
1.html中的canvas标签介绍：
<canvas> 是 HTML 中的一个图形绘制标签，它提供了一个可以通过 JavaScript 绘制图形的区域。
<canvas> 标签定义了一个绘图区域，其大小由 width 和 height 属性决定。如果没有指定 width 和 height，默认值分别为 300px 和 150px。

一个实例说明(简单了解即可)：
<!DOCTYPE html>
<html>
<body>
  <canvas id="myCanvas" width="400" height="300"></canvas>
  <script>
    const canvas = document.getElementById("myCanvas");
    const ctx = canvas.getContext("2d");

    // 绘制渐变矩形
    const gradient = ctx.createLinearGradient(0, 0, 400, 0);
    gradient.addColorStop(0, "red");
    gradient.addColorStop(1, "blue");
    ctx.fillStyle = gradient;
    ctx.fillRect(50, 50, 200, 100);

    // 绘制圆形
    ctx.beginPath();
    ctx.arc(300, 150, 40, 0, Math.PI * 2, true);
    ctx.fillStyle = "green";
    ctx.fill();
  </script>
</body>
</html>

2.canvas toBlob用法：
canvas.toBlob() 是 HTML5 中的一个方法，用于将 <canvas> 元素的内容转换为一个 Blob 对象。这个方法非常适合用于将画布上的内容导出为图片文件（如 PNG 或 JPEG 格式），并进行保存或上传操作。

    canvas.toBlob(callback[, type[, quality]])
    参数：
    callback：回调函数，当 Blob 对象创建完成后会被调用，回调函数的参数是生成的 Blob 对象。
    type（可选）：指定生成图片的 MIME 类型，例如 'image/png' 或 'image/jpeg'。默认值是 'image/png'。
    quality（可选）：仅在 type 为 'image/jpeg' 或 'image/webp' 时有效，用于指定图片的质量，范围是 0 到 1，值越大质量越高。
    
    返回值：
    无返回值，但通过回调函数可以获取生成的 Blob 对象。

扩展内容：将 Canvas 内容上传到服务器

const canvas = document.getElementById("myCanvas");

// 调用 toBlob 方法
canvas.toBlob(function(blob) {
  const formData = new FormData();
  formData.append("file", blob, "canvas-image.jpg"); // 将 Blob 对象附加到表单数据中

  // 使用 fetch 或 XMLHttpRequest 上传到服务器
  fetch("https://example.com/upload", {
    method: "POST",
    body: formData
  })
  .then(response => response.json())
  .then(data => {
    console.log("上传成功:", data);
  })
  .catch(error => {
    console.error("上传失败:", error);
  });
}, "image/jpeg");


3.toBlob方法是一个异步方法：
canvas.toBlob() 是一个异步方法，这意味着回调函数会在 for 循环结束后执行。因此，在回调函数中直接使用 i 会导致 i 的值总是最后一个值（即 20）。
所以代码使用IIFE（立即执行函数表达式）封存当前 i 值，实现代码功能

*/
