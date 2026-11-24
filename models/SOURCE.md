# مصدر ملفات نموذج الرؤية / Vision model provenance

النموذج: [ggml-org/SmolVLM-500M-Instruct-GGUF](https://huggingface.co/ggml-org/SmolVLM-500M-Instruct-GGUF). يذكر سجل النموذج الرسمي أن الترخيص Apache-2.0، وأن النموذج يحتوي 0.4B معامل تقريبًا. يجب إبقاء ملف الأوزان وملف إسقاط الرؤية في المجلد نفسه.

Model: [ggml-org/SmolVLM-500M-Instruct-GGUF](https://huggingface.co/ggml-org/SmolVLM-500M-Instruct-GGUF). The upstream model card lists the Apache-2.0 license and about 0.4B parameters. Keep the weight file and its vision projector in the same directory.

- `SmolVLM-500M-Instruct-Q8_0.gguf` — 436,806,912 بايت، SHA-256: `9d4612de6a42214499e301494a3ecc2be0abdd9de44e663bda63f1152fad1bf4`
- `mmproj-SmolVLM-500M-Instruct-Q8_0.gguf` — 108,783,360 بايت، SHA-256: `d1eb8b6b23979205fdf63703ed10f788131a3f812c7b1f72e0119d5d81295150`

The `llama-cpp-python` MTMD handler requires version 0.3.38 or newer. The image used to exercise the vision path is `docs/vision-test.png`.
يتطلب معالج MTMD في `llama-cpp-python` الإصدار 0.3.38 أو أحدث. وتوجد صورة تجربة مسار الرؤية في `docs/vision-test.png`.
