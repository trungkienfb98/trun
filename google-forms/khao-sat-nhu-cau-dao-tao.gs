/**
 * Tạo Google Form "Khảo sát nhu cầu đào tạo - Doanh nghiệp khởi nghiệp".
 *
 * Cách dùng:
 *   1. Mở https://script.google.com -> Dự án mới.
 *   2. Xóa nội dung mặc định, dán toàn bộ file này vào, bấm Lưu.
 *   3. Chọn hàm "taoForm" -> bấm Chạy -> cấp quyền khi được hỏi.
 *   4. Xem đường link form trong mục "Nhật ký thực thi".
 *
 * Script điền câu hỏi vào form trống có sẵn (FORM_ID). Để trống FORM_ID
 * thì script tạo một form mới.
 */
var FORM_ID = '1zoRPAZB3ISq333eiKRPtNBApOk9cI4k6JMaYzqJ0QA4';

function taoForm() {
  var form = FORM_ID ? FormApp.openById(FORM_ID)
                     : FormApp.create('Khảo sát nhu cầu đào tạo - Doanh nghiệp khởi nghiệp');

  // Xóa câu hỏi cũ (nếu chạy lại) để không bị trùng.
  form.getItems().forEach(function (item) { form.deleteItem(item); });

  form.setTitle('PHIẾU KHẢO SÁT NHU CẦU ĐÀO TẠO DÀNH CHO DOANH NGHIỆP KHỞI NGHIỆP')
      .setDescription(
        'Kính gửi Quý Doanh nghiệp/Nhà sáng lập,\n\n' +
        'Nhằm xây dựng chương trình đào tạo, hỗ trợ khởi nghiệp sát với thực tế, chúng tôi trân trọng ' +
        'đề nghị Quý vị dành khoảng 10–15 phút hoàn thành phiếu khảo sát này. Mọi thông tin chỉ dùng ' +
        'cho mục đích thiết kế chương trình đào tạo và được bảo mật.\n\nXin chân thành cảm ơn!')
      .setConfirmationMessage('Xin chân thành cảm ơn sự hợp tác của Quý Doanh nghiệp!')
      .setProgressBar(true)
      .setAllowResponseEdits(true);

  var max3 = FormApp.createCheckboxValidation()
      .setHelpText('Vui lòng chọn tối đa 3 phương án.')
      .requireSelectAtMost(3).build();

  // ===== PHẦN I =====
  form.addSectionHeaderItem().setTitle('PHẦN I. THÔNG TIN CHUNG VỀ DOANH NGHIỆP');
  form.addTextItem().setTitle('1. Tên doanh nghiệp/dự án').setRequired(true);
  form.addTextItem().setTitle('2. Họ tên người trả lời').setRequired(true);
  form.addTextItem().setTitle('Chức vụ');
  form.addTextItem().setTitle('3. Số điện thoại').setRequired(true);
  form.addTextItem().setTitle('Email')
      .setValidation(FormApp.createTextValidation()
        .setHelpText('Vui lòng nhập email hợp lệ.').requireTextIsEmail().build());
  form.addTextItem().setTitle('4. Địa chỉ');
  form.addTextItem().setTitle('5. Năm thành lập/bắt đầu hoạt động')
      .setValidation(FormApp.createTextValidation()
        .setHelpText('Nhập năm, ví dụ 2023.').requireNumberBetween(1900, 2100).build());
  form.addMultipleChoiceItem().setTitle('6. Loại hình doanh nghiệp').setRequired(true)
      .setChoiceValues(['Hộ kinh doanh', 'Công ty TNHH', 'Công ty cổ phần', 'Hợp tác xã',
                        'Chưa đăng ký (đang ở giai đoạn ý tưởng/dự án)']);
  form.addMultipleChoiceItem().setTitle('7. Lĩnh vực hoạt động chính').setRequired(true)
      .setChoiceValues(['Nông nghiệp – chế biến nông sản', 'Sản xuất – công nghiệp',
                        'Thương mại – bán lẻ', 'Thương mại điện tử',
                        'Công nghệ thông tin – phần mềm', 'Du lịch – dịch vụ – ẩm thực',
                        'Giáo dục', 'Y tế – chăm sóc sức khỏe'])
      .showOtherOption(true);
  form.addMultipleChoiceItem().setTitle('8. Giai đoạn phát triển hiện tại').setRequired(true)
      .setChoiceValues(['Ý tưởng', 'Thử nghiệm sản phẩm (MVP)', 'Đã có doanh thu ổn định',
                        'Đang mở rộng quy mô', 'Đang gọi vốn']);
  form.addMultipleChoiceItem().setTitle('9. Số lượng lao động').setRequired(true)
      .setChoiceValues(['Dưới 5 người', '5–10 người', '11–50 người', 'Trên 50 người']);
  form.addMultipleChoiceItem().setTitle('10. Doanh thu bình quân năm gần nhất')
      .setChoiceValues(['Chưa có doanh thu', 'Dưới 1 tỷ đồng', '1–3 tỷ đồng',
                        '3–10 tỷ đồng', 'Trên 10 tỷ đồng']);

  // ===== PHẦN II =====
  form.addPageBreakItem().setTitle('PHẦN II. THỰC TRẠNG VÀ KHÓ KHĂN');
  form.addMultipleChoiceItem()
      .setTitle('11. Doanh nghiệp đã từng tham gia khóa đào tạo/hỗ trợ khởi nghiệp nào chưa?')
      .setRequired(true)
      .setChoiceValues(['Chưa từng', 'Đã tham gia 1–2 lần', 'Đã tham gia nhiều lần']);
  form.addTextItem().setTitle('Nếu có, tên khóa học/đơn vị tổ chức');
  form.addCheckboxItem()
      .setTitle('12. Những khó khăn lớn nhất doanh nghiệp đang gặp phải (chọn tối đa 3)')
      .setRequired(true)
      .setChoiceValues(['Thiếu vốn/khó tiếp cận nguồn vốn',
                        'Khó tìm kiếm khách hàng, mở rộng thị trường',
                        'Thiếu kiến thức quản trị, điều hành',
                        'Quản lý tài chính, kế toán, thuế',
                        'Tuyển dụng và giữ chân nhân sự',
                        'Hiểu biết pháp lý (thủ tục, hợp đồng, sở hữu trí tuệ)',
                        'Ứng dụng công nghệ, chuyển đổi số',
                        'Xây dựng thương hiệu, marketing',
                        'Phát triển sản phẩm, đổi mới sáng tạo'])
      .showOtherOption(true)
      .setValidation(max3);

  // ===== PHẦN III =====
  form.addPageBreakItem().setTitle('PHẦN III. NHU CẦU NỘI DUNG ĐÀO TẠO')
      .setHelpText('13. Xin đánh giá mức độ cần thiết của các nội dung đào tạo sau.\n' +
                   '1 = Không cần thiết; 2 = Ít cần thiết; 3 = Bình thường; 4 = Cần thiết; 5 = Rất cần thiết');
  var thang = ['1', '2', '3', '4', '5'];
  var nhom = [
    ['A. Khởi sự và chiến lược kinh doanh', [
      'Kiểm định ý tưởng, xây dựng mô hình kinh doanh (Business Model Canvas, Lean Startup)',
      'Lập kế hoạch kinh doanh',
      'Nghiên cứu thị trường, phân tích đối thủ cạnh tranh']],
    ['B. Tài chính và gọi vốn', [
      'Quản trị tài chính, dòng tiền cho doanh nghiệp nhỏ',
      'Kế toán, thuế cơ bản',
      'Kỹ năng gọi vốn, thuyết trình với nhà đầu tư (Pitching)',
      'Tiếp cận vốn vay ngân hàng, quỹ hỗ trợ, chính sách ưu đãi của Nhà nước']],
    ['C. Marketing và bán hàng', [
      'Xây dựng thương hiệu',
      'Marketing số (Facebook, TikTok, Zalo, Google, SEO)',
      'Kỹ năng bán hàng, chăm sóc khách hàng',
      'Kinh doanh trên sàn thương mại điện tử, livestream bán hàng']],
    ['D. Quản trị và nhân sự', [
      'Kỹ năng lãnh đạo, quản lý đội nhóm',
      'Tuyển dụng, đào tạo, xây dựng chính sách nhân sự',
      'Xây dựng quy trình vận hành, quản trị chất lượng']],
    ['E. Pháp lý, công nghệ và đổi mới sáng tạo', [
      'Pháp luật doanh nghiệp, hợp đồng, lao động',
      'Sở hữu trí tuệ, bảo hộ nhãn hiệu',
      'Chuyển đổi số, ứng dụng phần mềm quản lý',
      'Ứng dụng trí tuệ nhân tạo (AI) trong kinh doanh',
      'Đổi mới sáng tạo, phát triển sản phẩm mới',
      'Xuất khẩu, tiêu chuẩn chất lượng (OCOP, VietGAP, ISO…)']]
  ];
  nhom.forEach(function (n) {
    form.addGridItem().setTitle(n[0]).setRows(n[1]).setColumns(thang).setRequired(true);
  });
  form.addParagraphTextItem().setTitle('14. Nội dung đào tạo khác mà doanh nghiệp quan tâm');

  // ===== PHẦN IV =====
  form.addPageBreakItem().setTitle('PHẦN IV. HÌNH THỨC VÀ TỔ CHỨC ĐÀO TẠO');
  form.addCheckboxItem().setTitle('15. Đối tượng cần được đào tạo trong doanh nghiệp').setRequired(true)
      .setChoiceValues(['Chủ doanh nghiệp/nhà sáng lập', 'Cán bộ quản lý',
                        'Nhân viên kinh doanh – marketing', 'Nhân viên kế toán – hành chính',
                        'Nhân viên kỹ thuật – sản xuất']);
  form.addMultipleChoiceItem().setTitle('16. Số người dự kiến tham gia đào tạo').setRequired(true)
      .setChoiceValues(['1 người', '2–3 người', '4–5 người', 'Trên 5 người']);
  form.addCheckboxItem().setTitle('17. Hình thức đào tạo mong muốn').setRequired(true)
      .setChoiceValues(['Lớp học trực tiếp', 'Học trực tuyến (online)',
                        'Kết hợp trực tiếp và trực tuyến', 'Hội thảo, tọa đàm chuyên đề',
                        'Tư vấn, cố vấn 1-1 (mentoring/coaching)',
                        'Tham quan, học tập mô hình thực tế']);
  form.addMultipleChoiceItem().setTitle('18. Thời lượng phù hợp cho một khóa học').setRequired(true)
      .setChoiceValues(['1 buổi', '1–2 ngày', '3–5 ngày', 'Học theo chuỗi nhiều tuần']);
  form.addCheckboxItem().setTitle('19. Thời gian thuận lợi để tham gia').setRequired(true)
      .setChoiceValues(['Ngày thường – giờ hành chính', 'Buổi tối ngày thường', 'Cuối tuần']);
  form.addTextItem().setTitle('20. Địa điểm thuận tiện');
  form.addMultipleChoiceItem()
      .setTitle('21. Mức chi phí doanh nghiệp sẵn sàng chi trả cho một khóa học/người').setRequired(true)
      .setChoiceValues(['Chỉ tham gia khóa miễn phí/được hỗ trợ', 'Dưới 1 triệu đồng',
                        '1–3 triệu đồng', '3–5 triệu đồng', 'Trên 5 triệu đồng']);
  form.addCheckboxItem()
      .setTitle('22. Yếu tố quan trọng nhất khi lựa chọn khóa đào tạo (chọn tối đa 3)').setRequired(true)
      .setChoiceValues(['Giảng viên có kinh nghiệm thực tiễn',
                        'Nội dung sát thực tế, áp dụng được ngay', 'Chi phí hợp lý',
                        'Được cấp chứng nhận', 'Cơ hội kết nối, mở rộng quan hệ',
                        'Có hỗ trợ sau đào tạo'])
      .setValidation(max3);

  // ===== PHẦN V =====
  form.addPageBreakItem().setTitle('PHẦN V. NHU CẦU HỖ TRỢ KHÁC VÀ Ý KIẾN ĐÓNG GÓP');
  form.addCheckboxItem().setTitle('23. Ngoài đào tạo, doanh nghiệp còn có nhu cầu hỗ trợ nào khác?')
      .setChoiceValues(['Kết nối nhà đầu tư, quỹ đầu tư', 'Kết nối đối tác, khách hàng',
                        'Tư vấn pháp lý, thủ tục',
                        'Tham gia hội chợ, triển lãm, xúc tiến thương mại',
                        'Không gian làm việc chung, vườn ươm', 'Tham gia cuộc thi khởi nghiệp'])
      .showOtherOption(true);
  form.addParagraphTextItem().setTitle('24. Ý kiến đóng góp, đề xuất khác');
  form.addMultipleChoiceItem()
      .setTitle('25. Doanh nghiệp có muốn nhận thông tin về các chương trình đào tạo sắp tới không?')
      .setRequired(true)
      .setChoiceValues(['Có', 'Không']);

  Logger.log('Link chỉnh sửa: ' + form.getEditUrl());
  Logger.log('Link gửi khảo sát: ' + form.getPublishedUrl());
}
